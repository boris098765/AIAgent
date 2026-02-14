import subprocess
import threading
import queue
from core.runtime.workspace import Workspace

class ShellSession:
    def __init__(self):
        self.workspace = Workspace()
        self.workspace.chdir()

        self.process = subprocess.Popen(
            ["/bin/bash"],
            cwd=self.workspace.root,
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

    def execute(self, command: str):
        marker = "__END__"
        self.process.stdin.write(f"{command}\necho {marker}\n")
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
