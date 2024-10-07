import os
import shutil

def clean_directory(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if name != '.gitkeep':
                file_path = os.path.join(root, name)
                try:
                    os.remove(file_path)
                except PermissionError:
                    print(f"Warning: Unable to remove file {file_path}. It may be in use.")
                except Exception as e:
                    print(f"Error removing file {file_path}: {str(e)}")
        
        for name in dirs:
            path = os.path.join(root, name)
            try:
                if not os.listdir(path):
                    os.rmdir(path)
            except Exception as e:
                print(f"Error removing directory {path}: {str(e)}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    if os.path.exists(data_dir):
        print(f"Cleaning {data_dir}...")
        clean_directory(data_dir)
    else:
        print(f"Directory not found: {data_dir}")

    print("Clean up completed.")

if __name__ == "__main__":
    main()