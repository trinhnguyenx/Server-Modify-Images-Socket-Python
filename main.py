import socket
import os
import cv2
import requests

# Function to process image: add text
def process_image(img):
    text = "Hello, OpenCV!"
    font = cv2.FONT_HERSHEY_SIMPLEX
    bottom_left_corner = (10, img.shape[0] - 10)
    font_scale = 1
    font_color = (255, 255, 255)  # White color
    line_type = 2
    cv2.putText(img, text, bottom_left_corner, font, font_scale, font_color, line_type)
    return img

# Function to download image from URL
def download_image(url, file_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(2048):
                file.write(chunk)
    else:
        raise Exception("Failed to download image")

# Create a directory to save images if it doesn't exist
image_folder = 'images'
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
server.bind(('0.0.0.0', 5002)) 
server.listen(1)

while True:
    client_socket, client_address = server.accept()
    print(f"Connected to client {client_address}")

    # Receive data type (IMAGE or URL)  
    data_type = client_socket.recv(4)
    
    if data_type == b"IMG ":
    # Receive image data from client and save it
        file_name = f"{image_folder}/image_{client_address[0]}_{client_address[1]}.jpg"
        with open(file_name, 'wb') as file:
            while True:
                image_chunk = client_socket.recv(2048)
                if image_chunk.endswith(b"EOF"):
                    file.write(image_chunk[:-3]) 
                    break
                file.write(image_chunk)

        print(f"Image received from {client_address} and saved as {file_name}")

        img = cv2.imread(file_name)
        edited_img = process_image(img)
        edited_file_name = f"{image_folder}/edited_image_{client_address[0]}_{client_address[1]}.jpg"
        cv2.imwrite(edited_file_name, edited_img)

        # Kiểm tra kết nối trước khi gửi dữ liệu trả về
        if client_socket.fileno() != -1:
            with open(edited_file_name, 'rb') as edited_file:
                edited_image_data = edited_file.read()
                client_socket.sendall(edited_image_data)

            print(f"Edited image sent back to {client_address}")
        else:
            print("Connection closed by client.")


    elif data_type == b"URL ":
        # Receive URL data from client
        received_data = b''
        while True:
            chunk = client_socket.recv(2048)
            if chunk.endswith(b"EOF"):
                received_data += chunk[:-3]
                break
            received_data += chunk
        
        image_url = received_data.decode('utf-8')
        print(f"URL received from {client_address}: {image_url}")

        # Download image from the URL
        file_name = f"{image_folder}/image_{client_address[0]}_{client_address[1]}.jpg"
        try:
            download_image(image_url, file_name)
            print(f"Image downloaded and saved as {file_name}")

            # Read the downloaded image, process it, and save the edited image
            img = cv2.imread(file_name)
            edited_img = process_image(img)
            edited_file_name = f"{image_folder}/edited_image_{client_address[0]}_{client_address[1]}.jpg"
            cv2.imwrite(edited_file_name, edited_img)

            # Send the edited image back to the client
            with open(edited_file_name, 'rb') as edited_file:
                edited_image_data = edited_file.read()
                client_socket.sendall(edited_image_data)

            print(f"Edited image sent back to {client_address}")
        except Exception as e:
            print(f"Failed to download image: {e}")
            client_socket.sendall(b"Failed to download image")

    client_socket.close()

