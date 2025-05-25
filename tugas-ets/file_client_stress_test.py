import socket
import json
import base64
import logging
import os
import concurrent.futures
import time
import random
import threading
import multiprocessing
import pandas as pd
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CLIENT] - %(levelname)s - %(message)s')

server_address = ('172.16.16.101', 6677)

STATISTICS_FILE = "stress_test_results.csv"


def send_command(command_str=""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)

        full_command_str = command_str + "\r\n\r\n"
        sock.sendall(full_command_str.encode())

        data_received = ""
        while True:
            data = sock.recv(1024 * 1024)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break

        if not data_received:
            return {'status': 'ERROR', 'data': 'No data received from server'}

        json_part, _, _ = data_received.partition("\r\n\r\n")
        cleaned_data = json_part.strip()

        if not cleaned_data:
            return {'status': 'ERROR', 'data': 'Empty parsable data from server'}

        hasil = json.loads(cleaned_data)
        return hasil
    except json.JSONDecodeError as e:
        return {'status': 'ERROR', 'data': f"JSON decode error: {e}"}
    except Exception as e:
        return {'status': 'ERROR', 'data': str(e)}
    finally:
        if sock:
            sock.close()


def remote_list():
    command_str = f"LIST"
    hasil = send_command(command_str)
    if (hasil and hasil.get('status') == 'OK'):
        logging.info("daftar file : ")
        for nmfile in hasil['data']:
            logging.info(f"- {nmfile}")
        return True
    else:
        logging.error(f"List failed: {hasil}")
        return False


def remote_get(filename=""):
    if not filename:
        return False, None

    command_str = f"GET {filename}"
    hasil = send_command(command_str)

    if hasil and hasil.get('status') == 'OK':
        try:
            namafile = hasil.get('data_namafile')
            isifile_b64 = hasil.get('data_file')

            if not namafile or not isifile_b64:
                return False, None

            isifile = base64.b64decode(isifile_b64)
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            local_filename = os.path.join(temp_dir,
                                          f"downloaded_{threading.current_thread().name}_{os.path.basename(namafile)}_{random.randint(1, 1000)}.bin")

            with open(local_filename, 'wb') as fp:
                fp.write(isifile)
            logging.info(
                f"[THREAD {threading.current_thread().name}] GET {filename}: Successfully downloaded as {local_filename}")
            return True, local_filename
        except (KeyError, base64.binascii.Error, Exception) as e:
            logging.error(
                f"[THREAD {threading.current_thread().name}] GET {filename}: Error processing downloaded file: {e}")
            return False, None
    else:
        logging.error(f"[THREAD {threading.current_thread().name}] GET {filename}: Failed. Response: {hasil}")
        return False, None


def remote_upload(filename=""):
    if not os.path.isfile(filename):
        return False

    try:
        fn = os.path.basename(filename)
        with open(filename, 'rb') as fp:
            encoded_file = base64.b64encode(fp.read()).decode()

        result = send_command(f"UPLOAD {fn} {encoded_file}")

        if result and result.get('status') == 'OK':
            logging.info(f"[THREAD {threading.current_thread().name}] UPLOAD {filename}: Successfully uploaded.")
            return True
        else:
            logging.error(f"[THREAD {threading.current_thread().name}] UPLOAD {filename}: Failed. Response: {result}")
            return False
    except Exception as e:
        logging.error(f"[THREAD {threading.current_thread().name}] UPLOAD {filename}: Error during upload process: {e}")
        return False


def remote_delete(filename=""):
    if not filename:
        return False

    hasil = send_command(f"DELETE {filename}")

    if hasil and hasil.get('status') == 'OK':
        logging.info(f"[THREAD {threading.current_thread().name}] DELETE {filename}: Successfully deleted.")
        return True
    else:
        logging.error(f"[THREAD {threading.current_thread().name}] DELETE {filename}: Failed. Response: {hasil}")
        return False


def get_local_files(list_of_filename=[]):
    found_files = []
    for filename in list_of_filename:
        if os.path.isfile(filename):
            found_files.append(filename)
        else:
            logging.warning(f"File not found: {filename}. Please create it to run the test.")
    if not found_files:
        logging.error("None of the specified files were found. Cannot proceed with tests.")
    return found_files


def client_worker_task(worker_id, host, port, operation_type, file_path_to_test):
    current_executor_name = multiprocessing.current_process().name if multiprocessing.current_process().name != 'MainProcess' else threading.current_thread().name

    successful_operations = 0
    failed_operations = 0
    total_bytes_processed = 0
    start_time_worker = time.time()

    file_name_on_server = os.path.basename(file_path_to_test)
    file_size = os.path.getsize(file_path_to_test)
    downloaded_file_path = None

    try:
        if operation_type == "UPLOAD":
            logging.info(f"[{current_executor_name}] Worker {worker_id}: Attempting UPLOAD '{file_path_to_test}'.")
            upload_success = remote_upload(file_path_to_test)
            if upload_success:
                successful_operations += 1
                total_bytes_processed += file_size
            else:
                failed_operations += 1

        elif operation_type == "DOWNLOAD":
            logging.info(f"[{current_executor_name}] Worker {worker_id}: Attempting DOWNLOAD '{file_name_on_server}'.")
            download_success, downloaded_file_path = remote_get(file_name_on_server)
            if download_success:
                successful_operations += 1
                total_bytes_processed += file_size
            else:
                failed_operations += 1

        else:
            logging.error(f"[{current_executor_name}] Worker {worker_id}: Invalid operation type: {operation_type}")
            failed_operations += 1

    except Exception as e:
        failed_operations += 1
        logging.error(
            f"[{current_executor_name}] Worker {worker_id}: An error occurred during {operation_type} of '{file_path_to_test}': {e}")
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            try:
                os.remove(downloaded_file_path)
            except OSError as e:
                logging.error(
                    f"[{current_executor_name}] Worker {worker_id}: Error deleting downloaded file '{downloaded_file_path}': {e}")

    end_time_worker = time.time()
    duration = end_time_worker - start_time_worker

    return {
        'successful_ops': successful_operations,
        'failed_ops': failed_operations,
        'bytes_processed': total_bytes_processed,
        'duration': duration,
        'client_worker_id': worker_id
    }


def write_results_to_csv(result_row, test_number, is_header=False):
    fieldnames = [
        'Nomor',
        'Jenis Executor',
        'Operasi',
        'Volume File (MB)',
        'Jumlah Client Worker Pool',
        'Jumlah Server Worker Pool (Simulasi)',
        'Waktu Total per Client (s)',
        'Throughput per Client (bytes/s)',
        'Jumlah Worker Client Sukses',
        'Jumlah Worker Client Gagal',
        'Jumlah Worker Server Sukses (Simulasi)',
        'Jumlah Worker Server Gagal (Simulasi)'
    ]

    mode = 'w' if is_header else 'a'

    file_exists = os.path.exists(STATISTICS_FILE)
    write_header = not file_exists or (file_exists and os.stat(STATISTICS_FILE).st_size == 0) or is_header

    with open(STATISTICS_FILE, mode, newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        row_to_write = {k: result_row.get(k, '') for k in fieldnames}
        writer.writerow(row_to_write)

    logging.info(f"Test {test_number} results written to {STATISTICS_FILE}")


def run_test(executor_type, operation, file_path, num_client_workers, num_server_workers_simulated):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    logging.info(
        f"\n--- Starting test: {executor_type.upper()} | {operation} | {file_size_mb:.0f}MB | Client Workers: {num_client_workers} | Server Workers (simulated): {num_server_workers_simulated} ---")

    start_time_total = time.time()

    results = []

    if executor_type == "threading":
        Executor = concurrent.futures.ThreadPoolExecutor
    elif executor_type == "multiprocessing":
        Executor = concurrent.futures.ProcessPoolExecutor
    else:
        raise ValueError("executor_type must be 'threading' or 'multiprocessing'")

    try:
        with Executor(max_workers=num_client_workers) as executor:
            futures = [
                executor.submit(client_worker_task, i, server_address[0], server_address[1], operation, file_path)
                for i in range(num_client_workers)]

            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    logging.error(f'{executor_type.capitalize()} client worker task generated an exception: {exc}')
                    results.append({
                        'successful_ops': 0,
                        'failed_ops': 1,
                        'bytes_processed': 0,
                        'duration': 0.0,
                        'client_worker_id': -1
                    })
    except Exception as e:
        logging.critical(f"Error initializing or running {executor_type} pool: {e}")
        for _ in range(num_client_workers):
            results.append({
                'successful_ops': 0,
                'failed_ops': 1,
                'bytes_processed': 0,
                'duration': 0.0,
                'client_worker_id': -1
            })

    end_time_total = time.time()
    total_test_duration = end_time_total - start_time_total

    total_successful_client_ops = sum(r['successful_ops'] for r in results)
    total_failed_client_ops = sum(r['failed_ops'] for r in results)
    total_bytes_transferred = sum(r['bytes_processed'] for r in results)

    individual_client_durations = [r['duration'] for r in results if r['duration'] > 0]
    avg_duration_per_client = sum(individual_client_durations) / len(
        individual_client_durations) if individual_client_durations else 0

    individual_client_throughputs = [(r['bytes_processed'] / r['duration']) for r in results if r['duration'] > 0]
    avg_throughput_per_client = sum(individual_client_throughputs) / len(
        individual_client_throughputs) if individual_client_throughputs else 0

    overall_throughput_test_run = (total_bytes_transferred / total_test_duration) if total_test_duration > 0 else 0

    num_client_workers_success = sum(1 for r in results if r['successful_ops'] > 0 and r['failed_ops'] == 0)
    num_client_workers_failed = sum(1 for r in results if r['failed_ops'] > 0 or r['successful_ops'] == 0)

    num_server_workers_success = num_client_workers_success
    num_server_workers_failed = num_client_workers_failed

    logging.info(
        f"--- Test Finished: {executor_type.upper()} | {operation} | {file_size_mb:.0f}MB | Client Workers: {num_client_workers} | Server Workers (simulated): {num_server_workers_simulated} | Overal Throughput: {overall_throughput_test_run} ---")

    return {
        'Executor Type': executor_type.capitalize(),
        'Operasi': operation,
        'Volume File (MB)': f"{file_size_mb:.0f}",
        'Jumlah Client Worker Pool': num_client_workers,
        'Jumlah Server Worker Pool (Simulasi)': num_server_workers_simulated,
        'Waktu Total per Client (s)': f"{avg_duration_per_client:.4f}",
        'Throughput per Client (bytes/s)': f"{avg_throughput_per_client:.2f}",
        'Jumlah Worker Client Sukses': num_client_workers_success,
        'Jumlah Worker Client Gagal': num_client_workers_failed,
        'Jumlah Worker Server Sukses (Simulasi)': num_server_workers_success,
        'Jumlah Worker Server Gagal (Simulasi)': num_server_workers_failed,
        'Total Test Duration (s)': f"{total_test_duration:.4f}",
        'Total Bytes Transferred': total_bytes_transferred,
        'Total Client Ops Success': total_successful_client_ops,
        'Total Client Ops Failed': total_failed_client_ops
    }


def generate_file(filename, size_in_bytes):
    if os.path.exists(filename):
        return

    try:
        with open(filename, 'wb') as f:
            f.seek(size_in_bytes - 1)
            f.write(b'\0')
        print(f"File '{filename}' berhasil dibuat dengan ukuran {size_in_bytes} byte.")
    except IOError as e:
        print(f"Terjadi kesalahan saat membuat file '{filename}': {e}")


if __name__ == '__main__':
    temp_dir = "temp_downloads"
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    generate_file("test_10MB.bin", 10 * 1024 * 1024)
    generate_file("test_50MB.bin", 50 * 1024 * 1024)
    generate_file("test_100MB.bin", 100 * 1024 * 1024)

    operations = ["UPLOAD", "DOWNLOAD"]

    file_volumes = {
        "10MB": "test_10MB.bin",
        "50MB": "test_50MB.bin",
        "100MB": "test_100MB.bin"
    }
    client_worker_pools = [1, 5, 50]
    server_worker = 50

    # executor_types = ["threading", "multiprocessing"]
    executor_types = ["threading"]

    all_test_results = []
    test_number = 1

    results_for_df = []

    for executor_type in executor_types:
        for operation in operations:
            for volume_name, file_name in file_volumes.items():
                local_file_path = file_name
                if not os.path.exists(local_file_path):
                    logging.error(
                        f"Required file '{local_file_path}' not found for volume {volume_name}. Skipping this test combination.")
                    continue

                for client_workers in client_worker_pools:
                    logging.info(f"\n--- Running Combination {test_number}/{2 * 3 * 3} ---")
                    logging.info(f"  Executor: {executor_type.upper()}, Operation: {operation}, Volume: {volume_name}, "
                                 f"Client Pool: {client_workers}, Server Pool (Simulated): {server_worker}")

                    result = run_test(executor_type, operation, local_file_path, client_workers, server_worker)
                    result['Nomor'] = test_number
                    result['Jenis Executor'] = executor_type.capitalize()
                    results_for_df.append(result)
                    write_results_to_csv(result, test_number)
                    test_number += 1
                    time.sleep(1)

    df = pd.DataFrame(results_for_df)

    final_columns = [
        'Nomor',
        'Jenis Executor',
        'Operasi',
        'Volume File (MB)',
        'Jumlah Client Worker Pool',
        'Jumlah Server Worker Pool (Simulasi)',
        'Waktu Total per Client (s)',
        'Throughput per Client (bytes/s)',
        'Jumlah Worker Client Sukses',
        'Jumlah Worker Client Gagal',
        'Jumlah Worker Server Sukses (Simulasi)',
        'Jumlah Worker Server Gagal (Simulasi)'
    ]
    df = df[final_columns]

    df.to_csv(STATISTICS_FILE, index=False)
    logging.info(f"\nAll stress tests completed. Results saved to {STATISTICS_FILE}")

    print("\n--- Stress Test Results Summary ---")
    print(df.to_string())

    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)
        logging.info(f"Cleaned up temporary download directory: {temp_dir}")
