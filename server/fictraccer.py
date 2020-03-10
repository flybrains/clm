import subprocess
import time
import threading
import os
import signal

class FicTraccer(object):
    def __init__(self, shutdown, server_shutdown):
        self.shutdown = shutdown
        self.server_shutdown = server_shutdown

    def add_config_address(self, config_address):
        self.config_address = config_address

    def edit_config(self):
        if self.config_address is not None:
            p = subprocess.Popen("gedit {}".format(self.config_address), shell=True)
        else:
            p = subprocess.Popen("gedit ft/sample/config.txt", shell=True)

    def run_polls(self, process):
        self.running = True
        while True:
            if self.stop_button_event.isSet():
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                self.running = False
                break
            time.sleep(0.1)
            if (process.poll() is not None) and (self.running):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                break





    def run(self, ft_thread_done):
        if self.config_address is not None:
            p = subprocess.call("ft/bin/fictrac {}".format(self.config_address), shell=True)
        else:
            p = subprocess.Popen("ft/bin/fictrac ft/sample/config.txt", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        time.sleep(1)
        poll_thread = threading.Thread(target=self.run_polls, args=(p,))
        poll_thread.start()
        poll_thread.join()
        print('Done with FicTrac')
        ft_thread_done.set()






if __name__=="__main__":
    ft = FicTraccer()
