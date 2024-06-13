from flask import Flask, render_template, request
import socket
import os

app = Flask(__name__)

server_ip = '192.168.102.195'  
server_port = 5002

# Tạo thư mục để lưu ảnh đã chỉnh sửa nếu chưa tồn tại
edited_image_folder = 'static'
if not os.path.exists(edited_image_folder):
    os.makedirs(edited_image_folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']

    if not file:
        return 'No file uploaded.'

    if file.content_type.split('/')[0] != 'image' or file.content_length > 10 * 1024 * 1024:  
        return 'Invalid file.'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((server_ip, server_port))
            client.sendall(b"IMG ")
            # Gửi dữ liệu hình ảnh
            with file.stream as f:
                while True:
                    image_data = f.read(2048)
                    if not image_data:
                        break
                    client.sendall(image_data)
                
                # Gửi thông điệp kết thúc
                client.sendall(b"EOF")
                print('Sent data to server.')

            # Đợi nhận dữ liệu từ server
            received_data = b''
            print('Receiving data from server...')
            while True:
                data_chunk = client.recv(2048)
                if not data_chunk:
                    break
                received_data += data_chunk

            # Lưu ảnh đã chỉnh sửa từ server
            edited_image_path = os.path.join(edited_image_folder, 'received_image.jpg')
            with open(edited_image_path, 'wb') as received_image_file:
                received_image_file.write(received_data)

            message = 'File uploaded successfully.'
            return render_template('success.html', message=message)

        except Exception as e:
            error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message)

@app.route('/upload_url', methods=['POST'])
def upload_url():
    url = request.form['url']

    # Kiểm tra xem URL có tồn tại không
    if not url:
        return 'No URL provided.'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            client.connect((server_ip, server_port))

            client.send(b"URL ")

            client.send(url.encode() + b"EOF")
            print('URL sent')

            received_data = b''
            while True: 
                data_chunk = client.recv(2048)
                if not data_chunk:
                    break
                received_data += data_chunk
            
            edited_image_path = os.path.join(edited_image_folder, 'received_image.jpg')
            print(edited_image_path)
            with open(edited_image_path, 'wb') as received_image_file:
                received_image_file.write(received_data)
            
            message = 'File uploaded successfully.'
            return render_template('success.html', message=message)

        except Exception as e:
            error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
