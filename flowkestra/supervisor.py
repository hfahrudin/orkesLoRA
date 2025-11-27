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

class Supervisor:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.mlflow_uri = self.config.get('mlflow_uri', "http://localhost:5000")
        self.experiment_name = self.config.get('experiment_name', "default_experiment")
        self.manager = multiprocessing.Manager()
        self.worker_state = self.manager.dict()
        self.concurrency_units: List[Union[threading.Thread, multiprocessing.Process]] = []
        self.all_finished = threading.Event() 
        self._print_timing = 5
        self._initialize_workers()

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

            # Periodically print status until all workers are done
            while not all(f.done() for f in futures):
                time.sleep(self._print_timing)
                self.clear_screen()
                
                # 2. Print the table using the helper method
                self.print_status_table_setup(f"Worker Monitor ({self.experiment_name})")
                
                # Flush the output to ensure immediate update
                # (Important for in-place console updates)
                print("", end="", flush=True) 

            
            self.clear_screen()
            
            self.print_status_table_setup(f"Worker Monitor ({self.experiment_name})")

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
        worker = None  # Initialize worker to None or a default value

        if config['mode'] == 'local':
            worker = Worker(
                worker_id=unique_id,
                workdir=config['target_workdir'],
                origin_dir=config['workdir'],
                # The shared, process-safe Manager().dict()
                main_states=self.worker_state, 
                requirements=config['requirements'],
                pipelines=config.get('pipelines'),
                experiment_name=self.experiment_name,
                mlflow_uri=self.mlflow_uri,
                ssh_config=None
            )
        
        elif config['mode'] == 'remote':
            # You MUST define what happens here, otherwise 'worker' remains None.
            # Example: Initialize a RemoteWorker class
            worker = Worker(
                worker_id=unique_id,
                workdir=config['target_workdir'],
                origin_dir=config['workdir'],
                main_states=self.worker_state,
                requirements=config['requirements'],
                pipelines=config.get('pipelines'),
                experiment_name=self.experiment_name,
                mlflow_uri=self.mlflow_uri,
                # Pass the necessary SSH configuration for remote mode
                ssh_config=config['ssh']
            )
            
        else:
            # Handle unknown modes explicitly
            raise ValueError(f"Unknown worker mode: {config['mode']}")

        # Final check before returning
        if worker is None:
            # This should ideally be unreachable if all modes are handled,
            # but is a final safety net.
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
        
        # alive_count = 0
        
        # Print row for each concurrency unit
        for wid, state in self.worker_state.items():

            worker_id = wid
            display_id = worker_id[:MAX_ID_WIDTH]
            

            status = self.worker_state[worker_id]['status'] if worker_id in self.worker_state else "Unknown"


            row = f"| {display_id:<{MAX_ID_WIDTH}} | {status:<22} |"
            print(row)
            
        print(separator)
        # print(f"[Monitor] Workers Alive: {alive_count}/{len(self.concurrency_units)}")

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
            # status = "Alive" if is_alive else "Finished"

            status = self.worker_state[worker_id]['status'] if worker_id in self.worker_state else "Unknown"
            
            if is_alive:
                alive_count += 1

            row = f"| {display_id:<{MAX_ID_WIDTH}} | {status:<22} |"
            print(row)
            
        print(separator)
        print(f"[Monitor] Workers Alive: {alive_count}/{len(self.concurrency_units)}")
    
    # The monitor_workers method now uses the helper function
    def monitor_workers(self):
        """
        Runs in a separate thread and updates worker status 
        in-place by clearing the screen before each table print.
        """
        
        while not self.all_finished.is_set():
            # Wait for 1 second or until the 'finished' event is set
            finished_early = self.all_finished.wait(self._print_timing) 
            
            if finished_early:
                break # Exit loop if workers finished and event was set
            
            # 1. Clear the screen before printing the new table
            self.clear_screen()
            
            # 2. Print the table using the helper method
            self.print_status_table(f"Worker Monitor ({self.experiment_name})")
            
            # Flush the output to ensure immediate update
            # (Important for in-place console updates)
            print("", end="", flush=True) 
            
        # --- FINAL STATE ---
        # 1. Clear the screen one last time
        self.clear_screen()
        
        # 2. Print the final state table
        self.print_status_table("Final State (All Workers Finished)")


    def run_all(self):
        # 1. Initialize concurrency units
        for worker_id, worker_info in self.worker_state.items():
            worker: Worker = worker_info['obj'] 

            if worker_id == 'local':
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
            daemon=True, # Daemon ensures it doesn't block program exit if main thread crashes
            name="WorkerMonitor"
        )
        monitor_thread.start()

        # --- 3. Wait for all worker units (Threads/Processes) to complete ---
        for unit in self.concurrency_units:
            unit.join()

        # --- 4. Signal the monitor thread to stop ---
        self.all_finished.set()
        
        # Wait for the monitor to clean up and exit (optional, but good practice)
        monitor_thread.join()

        print("\nAll jobs were completed.")