#!/usr/bin/env python3
"""
Clear the queue folder (delete all generation files)
Usage: python clear.py
"""

import os
import shutil


def clear_queue():
    """Delete all files in the queue folder"""
    queue_folder = 'queue'
    state_file = '.convert_state'
    
    if not os.path.exists(queue_folder):
        print(f"Queue folder '{queue_folder}' does not exist. Nothing to clear.")
        return
    
    # Get list of files before deletion
    files = os.listdir(queue_folder)
    generation_files = [f for f in files if f.startswith('generation_') and f.endswith('.pt')]
    
    if not generation_files:
        print("Queue is already empty.")
        return
    
    print(f"Found {len(generation_files)} file(s) in queue:")
    for f in sorted(generation_files):
        print(f"  {f}")
    
    # Confirm deletion
    response = input("\nAre you sure you want to delete all queue files? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled. Queue not cleared.")
        return
    
    # Delete all files in queue folder
    deleted_count = 0
    for f in files:
        file_path = os.path.join(queue_folder, f)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted_count += 1
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    print(f"\nDeleted {deleted_count} file(s) from queue.")
    
    # Reset conversion state
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"Reset conversion state ({state_file}).")
    
    print("\nQueue cleared successfully!")
    print("Note: old_generations folder was not affected.")


def main():
    clear_queue()


if __name__ == "__main__":
    main()
