import os

# Specify the folder containing the video files
folder_path = r'C:\Users\amvk2\OneDrive\Documents\Santhu mini project\ISL_VIDEOS'

# Define the video file extensions you want to change
video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')

# Loop through all files in the specified folder
for filename in os.listdir(folder_path):
    # Check if the file has a video extension
    if filename.lower().endswith(video_extensions):
        # Create the full path to the file
        old_file_path = os.path.join(folder_path, filename)
        
        # Trim whitespace from the filename and convert to uppercase
        trimmed_filename = filename.strip()
        new_filename = trimmed_filename.upper()
        new_file_path = os.path.join(folder_path, new_filename)
        
        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f'Renamed: "{filename}" to "{new_filename}"')

print("All video files have been renamed to uppercase and trimmed.")