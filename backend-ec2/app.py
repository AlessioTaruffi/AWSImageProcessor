import boto3
import uuid
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

# --- CONFIGURAZIONE ---
BUCKET_NAME = 'cipa-storage-850029407617' 
SQS_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/850029407617/ImageProcessingQueue.fifo' 

@app.route('/health', methods=['GET'])
def health_check():
    # Fondamentale per l'Auto Scaling e il Load Balancer
    return jsonify({"status": "healthy"}), 200

@app.route('/process-image', methods=['POST'])
def process_image():
    # 1. Verifica che l'immagine sia presente
    if 'image' not in request.files:
        return jsonify({"error": "Nessuna immagine fornita nel campo 'image'"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Nome file vuoto"}), 400

    # 2. Ottieni e parsa la singola operazione richiesta dal campo 'operation'
    operation_str = request.form.get('operation', '{}')
    try:
        operation = json.loads(operation_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Formato JSON per 'operation' non valido"}), 400

    # Assicurati che l'utente non abbia passato una lista per sbaglio
    if isinstance(operation, list):
        return jsonify({"error": "Il server accetta una singola operazione come oggetto JSON, non una lista"}), 400

    # Validazione per assicurarsi che l'operazione sia tra quelle consentite
    allowed_ops = {'resize', 'blur', 'grayscale', 'rotate'}
    if operation.get('op') not in allowed_ops:
        return jsonify({"error": f"Operazione non supportata o mancante: {operation.get('op')}"}), 400

    # 3. Genera i metadati del Job
    job_id = str(uuid.uuid4())
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    image_key = f"inputs/{job_id}.{ext}"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 4. Salva l'immagine su S3
    try:
        s3.upload_fileobj(file, BUCKET_NAME, image_key)
    except Exception as e:
        return jsonify({"error": f"Errore durante il caricamento su S3: {str(e)}"}), 500

    # 5. Prepara il payload per la coda SQS (nota che ora 'operation' è singolare)
    sqs_message = {
        "job_id": job_id,
        "image_key": image_key,
        "timestamp": timestamp,
        "operation": operation
    }

    # 6. Scrivi il messaggio nella coda SQS
    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(sqs_message),
            # Parametro OBBLIGATORIO per le code SQS FIFO:
            MessageGroupId="ImageProcessingGroup"
        )
    except Exception as e:
        return jsonify({"error": f"Errore durante l'invio a SQS: {str(e)}"}), 500

    # 7. Ritorna successo al client
    return jsonify({
        "status": "success",
        "message": "Immagine caricata e job accodato",
        "job_id": job_id,
        "image_key": image_key
    }), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)