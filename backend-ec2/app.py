import boto3
from flask import Flask, jsonify, request

app = Flask(__name__)

# Client AWS (verranno autenticati tramite IAM Role dell'istanza)
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

@app.route('/health', methods=['GET'])
def health_check():
    # Fondamentale per l'Auto Scaling e il Load Balancer
    return jsonify({"status": "healthy"}), 200

@app.route('/s3', methods=['POST'])
def manage_s3():
    # Esempio: Scrittura su S3
    s3.put_object(Bucket='tuo-bucket-name', Key='test.txt', Body='Hello World')
    return "File caricato", 200

@app.route('/sqs', methods=['GET'])
def manage_sqs():
    # Esempio: Lettura da SQS
    # response = sqs.receive_message(QueueUrl='tua-url-coda')
    return "Operazione SQS eseguita", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)