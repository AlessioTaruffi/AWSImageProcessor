#!/usr/bin/env bash
# Deploy della Lambda image processor del progetto CIPA.
#
# Prerequisiti:
#   - AWS CLI configurato con profile `cipa`
#   - Pat ha già creato bucket S3, Matt la coda SQS
#   - Variabili sotto compilate
#
# Uso (dalla root del repo): ./deploy.sh
# Idempotente: se la Lambda esiste, la aggiorna.

set -euo pipefail

# =========================================
# CONFIG — adatta questi valori
# =========================================
PROFILE="cipa"
REGION="us-east-1"
ACCOUNT_ID="850029407617"   # account Learner Lab
LAB_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/LabRole"

# Bucket S3 unico del progetto (chiedere a Pat il nome esatto)
S3_BUCKET="cipa-storage-${ACCOUNT_ID}"

# Coda SQS di Matt
SQS_QUEUE_ARN="arn:aws:sqs:${REGION}:${ACCOUNT_ID}:ImageProcessingQueue.fifo"

# Pillow layer (Klayers, Python 3.11, x86_64, us-east-1)
# ARN aggiornato qui: https://api.klayers.cloud/api/v2/p3.11/layer/latest/us-east-1/Pillow
PILLOW_LAYER_ARN="arn:aws:lambda:${REGION}:770693421928:layer:Klayers-p311-Pillow:8"

LAMBDA_NAME="handler"
LAMBDA_DIR="lambda-processor"

# =========================================
# Detect Python: priorità a `py` (Windows) per evitare l'alias Microsoft Store
# =========================================
PY=""
for candidate in py python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        # Verifica che funzioni davvero (non un alias Microsoft Store)
        if "$candidate" --version >/dev/null 2>&1; then
            PY="$candidate"
            break
        fi
    fi
done
 
if [[ -z "$PY" ]]; then
    echo "ERROR: Python non trovato. Installalo da python.org o disabilita l'app alias dal Microsoft Store."
    exit 1
fi
echo ">>> Using Python: $PY"


# =========================================
# Build dello ZIP usando Python (cross-platform)
# =========================================
echo ">>> Building $LAMBDA_NAME..."
cd "$LAMBDA_DIR"
rm -f function.zip
"$PY" -c "
import zipfile
with zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write('handler.py')
    z.write('processor.py')
print('  function.zip created')
"
cd ..


# =========================================
# Deploy (create or update)
# =========================================
ENV_VARS="Variables={S3_BUCKET=${S3_BUCKET},OUTPUT_PREFIX=outputs/}"

if aws lambda get-function --profile "$PROFILE" --function-name "$LAMBDA_NAME" >/dev/null 2>&1; then
    echo ">>> Updating $LAMBDA_NAME code..."
    aws lambda update-function-code \
        --profile "$PROFILE" \
        --function-name "$LAMBDA_NAME" \
        --zip-file "fileb://${LAMBDA_DIR}/function.zip" \
        >/dev/null
    aws lambda wait function-updated --profile "$PROFILE" --function-name "$LAMBDA_NAME"

    echo ">>> Updating $LAMBDA_NAME config..."
    aws lambda update-function-configuration \
        --profile "$PROFILE" \
        --function-name "$LAMBDA_NAME" \
        --memory-size 1024 \
        --timeout 25 \
        --environment "$ENV_VARS" \
        --layers "$PILLOW_LAYER_ARN" \
        >/dev/null
else
    echo ">>> Creating $LAMBDA_NAME..."
    aws lambda create-function \
        --profile "$PROFILE" \
        --function-name "$LAMBDA_NAME" \
        --runtime python3.11 \
        --handler handler.lambda_handler \
        --role "$LAB_ROLE_ARN" \
        --zip-file "fileb://${LAMBDA_DIR}/function.zip" \
        --memory-size 1024 \
        --timeout 25 \
        --environment "$ENV_VARS" \
        --layers "$PILLOW_LAYER_ARN" \
        >/dev/null
    aws lambda wait function-active --profile "$PROFILE" --function-name "$LAMBDA_NAME"
fi

# =========================================
# Trigger SQS
# =========================================
echo ">>> Wiring SQS trigger..."
aws lambda create-event-source-mapping \
    --profile "$PROFILE" \
    --function-name "$LAMBDA_NAME" \
    --event-source-arn "$SQS_QUEUE_ARN" \
    --batch-size 5 \
    --function-response-types ReportBatchItemFailures \
    >/dev/null 2>&1 || echo "    (trigger SQS già presente)"

echo ""
echo "✓ Deploy completed."
echo "  $LAMBDA_NAME (memory=1024MB, timeout=25s)"
echo "  S3_BUCKET=$S3_BUCKET"
echo "  trigger: SQS $SQS_QUEUE_ARN (batch=5, report-failures=on)"
