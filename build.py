import os
import platform
import subprocess
import shutil

def build_executable():
    system = platform.system().lower()
    output_dir = os.path.join('dist', system)
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    if system == 'windows':
        subprocess.run(['python', '-m', 'PyInstaller', '--onefile', '--clean',
                       '--distpath', output_dir, '--add-data', 'config.yaml;.',
                       'gui.py'], check=True)
        print(f'Windows build complete! Executable can be found in {output_dir}')
    else:
        # For Linux builds using Docker
        subprocess.run(['docker', 'build', '-t', 'cmake-to-bazel-builder', '.'], check=True)
        os.makedirs(output_dir, exist_ok=True)
        container_id = subprocess.run(['docker', 'create', 'cmake-to-bazel-builder'],
                                   capture_output=True, text=True).stdout.strip()
        subprocess.run(['docker', 'cp',
                       f'{container_id}:/app/dist/main',
                       os.path.join(output_dir, 'cmake-to-bazel')], check=True)
        subprocess.run(['docker', 'rm', container_id], check=True)
        print(f'Linux build complete! Executable can be found in {output_dir}')

if __name__ == '__main__':
    build_executable()