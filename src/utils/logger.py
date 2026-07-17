import os
import platform
import datetime

class ProcessLogger:
    def __init__(self):
        self.logs = []
        self.os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        self.api_call = "N/A"
        self.api_status = "N/A"
        self.zip_name = "N/A"
        self.tasks_status = {}

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] [{level}] {message}")

    def set_api_info(self, query: str, status: str):
        self.api_call = query
        self.api_status = status

    def set_zip_name(self, name: str):
        self.zip_name = name

    def set_task_status(self, task_name: str, success: bool, detail: str = ""):
        status_str = "SUCCESS" if success else "FAILED"
        if detail:
            self.tasks_status[task_name] = f"{status_str} ({detail})"
        else:
            self.tasks_status[task_name] = status_str

    def write_to_file(self, output_dir: str) -> str:
        """
        Writes the log to a timestamped file in the output directory.
        
        Returns:
            The absolute path to the written log file.
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{timestamp_str}.log"
        log_path = os.path.join(output_dir, log_filename)
        
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(" ZINIO MEDIA PROCESSOR EXECUTION LOG\n")
            f.write("=" * 60 + "\n")
            f.write(f"Execution Date/Time (Local): {datetime.datetime.now().isoformat()}\n")
            f.write(f"Operating System:            {self.os_info}\n")
            f.write(f"API Call Query:             {self.api_call}\n")
            f.write(f"API Call Status:            {self.api_status}\n")
            f.write(f"Incoming ZIP Name:          {self.zip_name}\n")
            f.write("-" * 60 + "\n")
            f.write("MAJOR TASK STATUS INDICATORS:\n")
            for task, status in self.tasks_status.items():
                f.write(f" - {task}: {status}\n")
            f.write("-" * 60 + "\n")
            f.write("LOG MESSAGES:\n")
            for entry in self.logs:
                f.write(entry + "\n")
            f.write("=" * 60 + "\n")
        return log_path
