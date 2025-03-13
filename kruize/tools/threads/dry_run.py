import argparse
import logging
import os
import subprocess
import sys
import time

def setup_logging():
    log_file = 'dry_run.log'
    if os.path.exists(log_file):
        os.remove(log_file)
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command, log_message, exit_on_fail=True):
    logging.info(log_message)
    print(log_message, end='')
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    while process.poll() is None:
        print('.', end='', flush=True)
        time.sleep(5)
    
    print(' Done.')
    stdout, stderr = process.communicate()
    logging.info(stdout.decode())
    if stderr:
        logging.error(stderr.decode())
    
    if process.returncode != 0 and exit_on_fail:
        print(f"✗ {log_message} failed")
        sys.exit(1)

def create_kind_cluster():
    logging.info("Creating KinD cluster 'dry-run'...")
    subprocess.run(['kind', 'create', 'cluster', '--name', 'dry-run'], check=True)
    print("✓ KinD cluster 'dry-run' created")

def delete_kind_cluster():
    logging.info("Deleting KinD cluster 'dry-run'...")
    subprocess.run(['kind', 'delete', 'cluster', '--name', 'dry-run'], check=True)
    print("✓ KinD cluster 'dry-run' deleted")

def clone_repo_branch(repo_url, repo_name, branch_name):
    if os.path.exists(repo_name):
        logging.info(f"Folder '{repo_name}' already exists. Skipping clone.")
        print(f"✓ '{repo_name}' already exists. Skipping clone.")
    else:
        logging.info(f"Cloning branch '{branch_name}' from {repo_url}...")
        subprocess.run(['git', 'clone', '-b', branch_name, repo_url], check=True)
        print(f"✓ {repo_name} branch '{branch_name}' cloned")

def install_autotune(autotune_repo_path, image):
    scripts_path = os.path.join(autotune_repo_path, "scripts")
    os.chdir(scripts_path)
    run_command([f'{scripts_path}/prometheus_on_kind.sh', '-as'], "Running ./scripts/prometheus_on_kind.sh")
    os.chdir(autotune_repo_path)
    run_command([f'{autotune_repo_path}/deploy.sh', '-c', 'minikube', '-m', 'crc', '-i', image],
                f"Running deploy.sh -c minikube -i {image}")

def main():
    parser = argparse.ArgumentParser(description="KinD Cluster and AutoTune Installer")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    init_parser = subparsers.add_parser('init', help='Initialize KinD cluster and install AutoTune')
    init_parser.add_argument('-i', '--image', default='quay.io/bharathappali/exman:latest',
                             help='AutoTune image to deploy (default: quay.io/bharathappali/exman:latest)')
    
    subparsers.add_parser('delete', help='Delete KinD cluster')
    
    args = parser.parse_args()
    setup_logging()
    
    if args.command == 'init':
        create_kind_cluster()
        autotune_repo_url = "https://github.com/kruize/autotune.git"
        autotune_repo_name = "autotune"
        autotune_repo_branch = "mvp_demo"
        clone_repo_branch(autotune_repo_url, autotune_repo_name, autotune_repo_branch)
        install_autotune(os.path.join(os.getcwd(), autotune_repo_name), args.image)
    elif args.command == 'delete':
        delete_kind_cluster()

if __name__ == "__main__":
    main()
