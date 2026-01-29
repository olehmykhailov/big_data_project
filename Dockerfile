# Use the AWS Lambda Python base image (Amazon Linux 2023 based)
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies into the Lambda task root
# This ensures Linux-compatible versions are installed
RUN pip install -r requirements.txt

# Copy project files explicitly to avoid copying local 'pip install -t' garbage
COPY database ${LAMBDA_TASK_ROOT}/database
COPY currencies.csv etl.py lambda_handler.py nbp_client.py wiki_parser.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler (filename.function_name)
CMD [ "lambda_handler.lambda_handler" ]
