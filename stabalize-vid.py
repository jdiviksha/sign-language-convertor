import os
import subprocess
import sys

def convert_and_stabilize_videos(folder_path):
    if not os.path.exists(folder_path):
        print("Error: The specified folder does not exist.")
        return
    
    files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
    
    if not files:
        print("No MP4 files found in the folder.")
        return
    
    stabilized_files = []
    
    for file in files:
        input_path = os.path.join(folder_path, file)
        stabilized_path = os.path.join(folder_path, "stabilized_" + file)
        output_path = os.path.join(folder_path, os.path.splitext(file)[0] + '.mov')

        # Step 1: Stabilize the video to keep the character centered
        stabilize_command = [
            'ffmpeg', '-i', input_path, '-vf', 'vidstabdetect=shakiness=5:accuracy=10',
            '-f', 'null', '-'
        ]
        subprocess.run(stabilize_command, check=True)

        stabilize_command_apply = [
            'ffmpeg', '-i', input_path, '-vf', 'vidstabtransform=smoothing=30',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-y', stabilized_path
        ]
        subprocess.run(stabilize_command_apply, check=True)
        
        stabilized_files.append(stabilized_path)

    # Step 2: Apply enhanced morph transitions
    transition_duration = 0.5  # 0.5 seconds before and after
    enhanced_transition = "xfade=transition=smoothleft:duration=0.5:offset=4.5"  # Smooth morph effect

    for i in range(len(stabilized_files) - 1):
        input1 = stabilized_files[i]
        input2 = stabilized_files[i + 1]
        output_transition = os.path.join(folder_path, f'transition_{i}.mp4')

        transition_command = [
            'ffmpeg', '-i', input1, '-i', input2,
            '-filter_complex', enhanced_transition, '-y', output_transition
        ]
        subprocess.run(transition_command, check=True)

    print("Enhanced stabilization and morph transition applied.")

if __name__ == "__main__":
    convert_and_stabilize_videos(r"C:\Users\amvk2\OneDrive\Documents\Santhu mini project\ISL_VIDEOS")
