import boto3
import uuid
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from botocore.exceptions import ClientError 

app = Flask(__name__)

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

BUCKET_NAME = 'cipa-storage-850029407617' 
SQS_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/850029407617/ImageProcessingQueue.fifo' 

# --- ENDPOINT DI MONITORAGGIO ---
@app.route('/health', methods=['GET'])
def health_check():
    """Verifica lo stato del servizio per il Load Balancer o App Runner."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({"error": "Immagine mancante"}), 400
    
    file = request.files['image']
    
    # Leggiamo l'operazione
    operation_str = request.form.get('operation', '{}')
    try:
        operation_obj = json.loads(operation_str)
        operations_list = [operation_obj] if isinstance(operation_obj, dict) else operation_obj
    except json.JSONDecodeError:
        return jsonify({"error": "JSON non valido"}), 400

    job_id = str(uuid.uuid4())
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    image_key = f"inputs/{job_id}.{ext}"

    # 1. Upload su S3
    s3.upload_fileobj(file, BUCKET_NAME, image_key)

    # 2. Invio a SQS
    sqs_message = {
        "job_id": job_id,
        "image_key": image_key,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "operations": operations_list
    }

    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(sqs_message),
        MessageGroupId="ImageProcessingGroup",
        MessageDeduplicationId=job_id
    )

    return jsonify({"status": "success", "job_id": job_id}), 202

@app.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    output_key = f"outputs/{job_id}.jpg"
    
    try:
        # Verifichiamo se il file esiste
        s3.head_object(Bucket=BUCKET_NAME, Key=output_key)
        
        # Genera URL per il download
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': output_key},
            ExpiresIn=3600
        )
        return jsonify({"status": "completed", "download_url": url}), 200

    except ClientError as e:
        # Se 404 o 403, l'immagine non è ancora pronta o non esiste
        error_code = e.response['Error']['Code']
        if error_code in ["404", "403"]:
            return jsonify({"status": "processing"}), 202
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
    # curl -X POST http://54.83.161.69/process-image -F "image=@PathImmagine\colosseo.jpg" -F "operation={\"op\": \"rotate\", \"angle\": 90}"
    # curl -X GET http://54.83.161.69/result/0f47e82a-5471-4c0b-8fcf-b981e7f20494