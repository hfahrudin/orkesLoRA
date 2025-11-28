import yaml
import threading
import multiprocessing
from flowkestra.worker import Worker
import uuid
from flowkestra.schema import ConfigSchema
from typing import Dict, Any, List, Union, Tuple
import time
import os 
from concurrent.futures import ThreadPoolExecutor
import requests


class Supervisor:
    def __init__(self, config_path: str, visualize_progress=None, clear_screen_on_update=None, clean_workdir_after_run=None, suppress_runner_output=None):
        self.config = self._load_config(config_path)
        self.mlflow_uri = self.config.get('mlflow_uri', "http://localhost:5000")
        self.experiment_name = self.config.get('experiment_name', "default_experiment")
        
        # Prioritize CLI flags over config file settings
        self.visualize_progress = visualize_progress if visualize_progress is not None else self.config.get('visualize_progress', True)
        self.clear_screen_on_update = clear_screen_on_update if clear_screen_on_update is not None else self.config.get('clear_screen_on_update', True)
        self.clean_workdir_after_run = clean_workdir_after_run if clean_workdir_after_run is not None else self.config.get('clean_workdir_after_run', True)
        self.suppress_runner_output = suppress_runner_output if suppress_runner_output is not None else self.config.get('suppress_runner_output', True)

        self.manager = multiprocessing.Manager()
        self.worker_state = self.manager.dict()
        self.concurrency_units: List[Union[threading.Thread, multiprocessing.Process]] = []
        self.all_finished = threading.Event() 
        self._print_timing = 5
        if not self._check_mlflow_server(self.mlflow_uri):
            raise RuntimeError(f"MLflow server not reachable at {self.mlflow_uri}")
        self._initialize_workers()

    def _check_mlflow_server(self, uri: str) -> bool:
        """
        Verify that the MLflow server is alive by querying the /#/experiments endpoint.
        """
        try:
            response = requests.get(f"{uri}/#/experiments", timeout=3)
            return response.status_code == 200
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to connect to MLflow server at {uri}")
        
    def _initialize_workers(self):
        def init_worker(cfg):
            unique_id = str(uuid.uuid4())
            self.worker_state[unique_id] = self.manager.dict({
                'id': unique_id,
                'obj': None,
                'status': 'initializing'
            })
            worker = self._assign_worker(unique_id, cfg)
            self.worker_state[unique_id]['obj'] = worker

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(init_worker, cfg) for cfg in self.config['instances']]

            if self.visualize_progress:
                # Periodically print status until all workers are done
                while not all(f.done() for f in futures):
                    time.sleep(self._print_timing)
                    if self.clear_screen_on_update:
                        self.clear_screen()
                    
                    self.print_status_table_setup(f"Worker Monitor ({self.experiment_name})")
                    print("", end="", flush=True) 
                
                if self.clear_screen_on_update:
                    self.clear_screen()
                
                self.print_status_table_setup(f"Worker Monitor ({self.experiment_name})")
            else:
                # If no visualization, just wait for all initialization futures to complete
                for f in futures:
                    f.result() # This will also raise any exceptions from init_worker

    def _load_config(self, yaml_path: str) -> dict:
        with open(yaml_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        validated_config = ConfigSchema(**raw_config)
        return validated_config.model_dump()

    def clear_screen(self):
        """Clears the terminal screen."""
        # For Windows
        if os.name == 'nt':
            os.system('cls')
        # For Linux/Mac
        else:
            os.system('clear')

    def _assign_worker(self, id, config: Dict[str, Any]) -> Tuple[str, Worker]:
        unique_id = id
        worker = None

        # Arguments common to all worker types
        worker_args = {
            'worker_id': unique_id,
            'workdir': config['target_workdir'],
            'origin_dir': config['workdir'],
            'main_states': self.worker_state,
            'requirements': config['requirements'],
            'pipelines': config.get('pipelines'),
            'experiment_name': self.experiment_name,
            'mlflow_uri': self.mlflow_uri,
            'clean_workdir_after_run': self.clean_workdir_after_run,
            'suppress_output': self.suppress_runner_output
        }

        if config['mode'] == 'local':
            worker = Worker(**worker_args, ssh_config=None)
        
        elif config['mode'] == 'remote':
            # This assumes your Worker class can handle ssh_config when provided
            worker = Worker(**worker_args, ssh_config=config.get('ssh'))
            
        else:
            raise ValueError(f"Unknown worker mode: {config['mode']}")

        if worker is None:
            raise RuntimeError("Worker initialization failed unexpectedly.")
        
        return worker

    def print_status_table_setup(self, title: str):
        """Prints the worker status table once."""
        MAX_ID_WIDTH = 6
        
        print(f"--- {title} ---")
        print(f"[Monitor] Snapshot Time: {time.strftime('%H:%M:%S')}")
        
        # Table Header
        header = f"| {'ID':<{MAX_ID_WIDTH}} | {'STATUS':<22} |"
        separator = f"+{'-' * (MAX_ID_WIDTH + 2)}+{'-' * 24}+"
        
        print(separator)
        print(header)
        print(separator)
        
        # Print row for each concurrency unit
        for wid, state in self.worker_state.items():
            worker_id = wid
            display_id = worker_id[:MAX_ID_WIDTH]
            status = self.worker_state[worker_id]['status'] if worker_id in self.worker_state else "Unknown"
            row = f"| {display_id:<{MAX_ID_WIDTH}} | {status:<22} |"
            print(row)
            
        print(separator)

    def print_status_table(self, title: str):
        """Prints the worker status table once."""
        MAX_ID_WIDTH = 6
        
        print(f"--- {title} ---")
        print(f"[Monitor] Snapshot Time: {time.strftime('%H:%M:%S')}")
        
        # Table Header
        header = f"| {'ID':<{MAX_ID_WIDTH}} | {'STATUS':<22} |"
        separator = f"+{'-' * (MAX_ID_WIDTH + 2)}+{'-' * 24}+"
        
        print(separator)
        print(header)
        print(separator)
        
        alive_count = 0
        
        # Print row for each concurrency unit
        for unit in self.concurrency_units:
            worker_id = unit.name
            display_id = worker_id[:MAX_ID_WIDTH]
            
            is_alive = unit.is_alive()
            status = self.worker_state[worker_id]['status'] if worker_id in self.worker_state else "Unknown"
            
            if is_alive:
                alive_count += 1

            row = f"| {display_id:<{MAX_ID_WIDTH}} | {status:<22} |"
            print(row)
            
        print(separator)
        print(f"[Monitor] Workers Alive: {alive_count}/{len(self.concurrency_units)}")
    
    def monitor_workers(self):
        """
        Runs in a separate thread and updates worker status 
        in-place by clearing the screen before each table print.
        """
        if not self.visualize_progress:
            # If visualization is off, just wait for the signal to finish.
            self.all_finished.wait()
            return
        
        while not self.all_finished.is_set():
            finished_early = self.all_finished.wait(self._print_timing) 
            
            if finished_early:
                break
            
            if self.clear_screen_on_update:
                self.clear_screen()
            
            self.print_status_table(f"Worker Monitor ({self.experiment_name})")
            print("", end="", flush=True) 
            
        # --- FINAL STATE ---
        if self.clear_screen_on_update:
            self.clear_screen()
        
        self.print_status_table("Final State (All Workers Finished)")

    def run_all(self):
        # 1. Initialize concurrency units
        for worker_id, worker_info in self.worker_state.items():
            worker: Worker = worker_info['obj'] 

            # Use multiprocessing for local workers (no SSH client)
            # and threading for remote workers.
            if worker.ssh_client is None:
                unit = multiprocessing.Process(
                    target=worker.run, 
                    name=str(worker_id)
                )
            else:
                unit = threading.Thread(
                    target=worker.run, 
                    name=str(worker_id)
                )

            unit.start()
            self.concurrency_units.append(unit)

        # --- 2. Start the Monitor Thread ---
        monitor_thread = threading.Thread(
            target=self.monitor_workers, 
            daemon=True,
            name="WorkerMonitor"
        )
        monitor_thread.start()

        # --- 3. Wait for all worker units (Threads/Processes) to complete ---
        for unit in self.concurrency_units:
            unit.join()

        # --- 4. Signal the monitor thread to stop ---
        self.all_finished.set()
        
        monitor_thread.join()

        print("\nAll jobs were completed.")
