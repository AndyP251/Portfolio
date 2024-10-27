import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import json
from projectWebsite.settings import BUCKET_NAME, ACCOUNT_ID, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

class S3Utils:
    def __init__(self):
        self.bucket_name = BUCKET_NAME
        self.account_id = ACCOUNT_ID
        self.session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        self.s3_client = self.session.client('s3')

    def read_json_from_s3(self, object_name):
        """Read a JSON file from the S3 bucket and return its contents as a list of dictionaries."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
            json_data = response['Body'].read().decode('utf-8')
            data = json.loads(json_data)
            print(f'Successfully read {object_name} from {self.bucket_name}')
            return data
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')
    def upload_data_to_s3(self, data, object_name):
        """Upload data to the S3 bucket."""
        try:
            # Convert data to JSON string if it's a dict or list
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            
            # Ensure data is encoded as bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            response = self.s3_client.put_object(
                Body=data,
                Bucket=self.bucket_name,
                Key=object_name,
                ContentType='application/json'  # Specify content type
            )
            
            # Check if upload was successful
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print(f'Successfully uploaded data to {self.bucket_name}/{object_name}')
                return True
            else:
                print(f'Upload failed with response: {response}')
                return False
                
        except Exception as e:
            print(f'Error occurred: {e}')
            return False
    
    def upload_to_s3(self, file_name, object_name=None):
        """Upload a file to the S3 bucket."""
        if object_name is None:
            object_name = file_name
        try:
            self.s3_client.upload_file(file_name, self.bucket_name, object_name)
            print(f'Successfully uploaded {file_name} to {self.bucket_name}/{object_name}')
        except FileNotFoundError:
            print(f'The file {file_name} was not found.')
        except NoCredentialsError:
            print('Credentials not available.')
        except PartialCredentialsError:
            print('Incomplete credentials provided.')
        except Exception as e:
            print(f'Error occurred: {e}')

    def list_files_in_s3(self):
        """List files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            if 'Contents' in response:
                print('Files in bucket:')
                for obj in response['Contents']:
                    print(obj['Key'])
            else:
                print('Bucket is empty.')
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')

    def download_from_s3(self, object_name, file_name):
        """Download a file from the S3 bucket."""
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_name)
            print(f'Successfully downloaded {object_name} from {self.bucket_name} to {file_name}')
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')

    def delete_from_s3(self, object_name):
        """Delete a file from the S3 bucket."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            print(f'Successfully deleted {object_name} from {self.bucket_name}')
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')

    def get_object_size(self, object_name):
        """Get the size of an object in the S3 bucket."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
            size = response['ContentLength']
            print(f'Size of {object_name}: {size} bytes')
            return size
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')

    def copy_object(self, source_object, destination_object):
        """Copy an object within the same S3 bucket."""
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': source_object},
                Key=destination_object
            )
            print(f'Successfully copied {source_object} to {destination_object}')
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')

    def generate_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL for an object."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            print(f'Presigned URL for {object_name}: {url}')
            return url
        except NoCredentialsError:
            print('Credentials not available.')
        except Exception as e:
            print(f'Error occurred: {e}')
    def initialize_user_directory(self, user_id):
        """Initialize a directory structure for a user with empty JSON files."""
        try:
            # Define the directory path using the user_id
            user_directory = f'users/{user_id}/'
            
            # List of files to create in the user's directory
            files_to_create = [
                'schedule.json',
                'gradescopeTasks.json',
                'canvasTasks.json'
            ]
            
            # Initialize empty array as JSON string
            empty_array = json.dumps([])
            
            # Create each file in the user's directory
            for file_name in files_to_create:
                try:
                    # Combine directory path with file name
                    file_path = f'{user_directory}{file_name}'
                    
                    # Upload empty array as JSON to S3
                    self.s3_client.put_object(
                        Body=empty_array,
                        Bucket=self.bucket_name,
                        Key=file_path,
                        ContentType='application/json'
                    )
                    print(f'Successfully created {file_path} in {self.bucket_name}')
                    
                except Exception as e:
                    print(f'Error creating {file_path}: {e}')
                    return False
                    
            return True
            
        except Exception as e:
            print(f'Error in initialize_user_directory: {e}')
            return False
