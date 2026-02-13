import subprocess
import threading
import queue


class ShellSession:
    def __init__(self):
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.output_queue = queue.Queue()

        def reader():
            for line in self.process.stdout:
                self.output_queue.put(line)

        threading.Thread(target=reader, daemon=True).start()

    def execute(self, command: str, timeout: float = 5):
        marker = "__END__"
        full_command = f"{command}\necho {marker}\n"

        self.process.stdin.write(full_command)
        self.process.stdin.flush()

        output = []
        while True:
            line = self.output_queue.get()
            if marker in line:
                break
            output.append(line)

        return "".join(output)

    def close(self):
        self.process.terminate()
