import os
import subprocess
import sys

def convert_mp4_to_mov(folder_path):
    if not os.path.exists(folder_path):
        print("Error: The specified folder does not exist.")
        return
    
    files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
    
    if not files:
        print("No MP4 files found in the folder.")
        return
    
    for file in files:
        input_path = os.path.join(folder_path, file)
        output_path = os.path.join(folder_path, os.path.splitext(file)[0] + '.mov')
        
        command = [
            'ffmpeg', '-i', input_path, '-q:v', '0', '-q:a', '0', output_path
        ]
        
        try:
            subprocess.run(command, check=True)
            print(f"Converted: {file} -> {os.path.basename(output_path)}")
        except subprocess.CalledProcessError:
            print(f"Error converting {file}")

if __name__ == "__main__":
        convert_mp4_to_mov(r"C:\Users\amvk2\OneDrive\Documents\Santhu mini project\ISL_VIDEOS")
