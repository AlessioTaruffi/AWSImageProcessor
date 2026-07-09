
# Creazione di un'istanza  t4g.micro 

# 1. Recupera dinamicamente l'AMI più recente di Ubuntu 22.04 (ARM64)
$AMI_ID = aws ssm get-parameters `
  --names /aws/service/canonical/ubuntu/server/22.04/stable/current/arm64/hvm/ebs-gp2/ami-id `
  --region us-east-1 `
  --query "Parameters[0].Value" `
  --output text

Write-Host "AMI ID ufficiale trovato: $AMI_ID"

# 2. Lancio dell'istanza On-Demand (Rimosso l'opzione Spot)
$INSTANCE_ID = aws ec2 run-instances `
  --image-id $AMI_ID `
  --instance-type t4g.micro `
  --key-name vockey `
  --security-groups default `
  --region us-east-1 `
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Principal}]' `
  --query 'Instances[0].InstanceId' `
  --output text


# 3. Verifica
Write-Host "L'ID della tua istanza è: $INSTANCE_ID"


# id istanza creata =  i-01584101000c789ab
# ip istanza =  54.172.163.153 

#Recuperare indirizzo ip dell'istanza 
$ip = aws ec2 describe-instances `
  --instance-ids $INSTANCE_ID `
  --query "Reservations[0].Instances[0].PublicIpAddress" `
  --output text

  # Comando per aprire la porta 22 in entrata da tutti: porta SSH -> Sennò la connessione ssh fallirà
  aws ec2 authorize-security-group-ingress `
  --group-name default `
  --protocol tcp `
  --port 22 `
  --cidr 0.0.0.0/0 `
  --region us-east-1

  # Aggiunge il permesso di sola lettura per il tuo utente corrente per la chiave per fare la sessione ssh
  icacls "PathPem\labsuser.pem" /grant:r "$($env:USERNAME):(R)"

  # Collegarsi alla sessione remota
  ssh -i "PathPem\labsuser.pem" ubuntu@ip istanza preso prima

  # Eliminare istanza ec2
  aws ec2 terminate-instances --instance-ids "i-0dde53c13b856d399"

  # Fare AMI di istanza ec2 ami-0cc71e6aadb380f5c
  aws ec2 create-image --instance-id i-01584101000c789ab --name "Flask-Prod-AMI-%DATE:~-4%-%DATE:~3,2%-%DATE:~0,2%" --description "AMI con Flask auto-sync da S3" --no-reboot

  # Ottenere info su security group
  aws ec2 describe-security-groups --query "SecurityGroups[*].[GroupId, GroupName]" --output table

  # Ottenere info sull'iam role
  aws iam list-instance-profiles --query "InstanceProfiles[*].InstanceProfileName" --output table

  # Ottenere nomi chiave ssh
  aws ec2 describe-key-pairs --query "KeyPairs[*].KeyName" --output table

  # Ami di riferimento ami-0cc71e6aadb380f5c
  # aws ec2 run-instances --image-id ami-0cc71e6aadb380f5c --count 1 --instance-type t4g.micro --key-name vockey --security-group-ids sg-00df9675279784ad2 --iam-instance-profile Name=LabInstanceProfile --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=Primary}]"

  aws ec2 run-instances ^
    --image-id ami-0cc71e6aadb380f5c ^
    --count 1 ^
    --instance-typet4g.micro `
    --key-name vockey ^
    --security-group-ids sg-00df9675279784ad2 ^
    --iam-instance-profile Name=LabInstanceProfile ^
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=Secondary}]"