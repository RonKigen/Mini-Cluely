from PyQt5.QtCore import QThread, pyqtSignal


class TaskThread(QThread):
    result_signal = pyqtSignal(object)  # Return result signal

    progress_signal = pyqtSignal(str)  # Progress update signal
    finished_signal = pyqtSignal() # Task completion signal

    def __init__(self, task_func, *args, **kwargs):

        super().__init__()

        self.task_func = task_func

        self.args = args

        self.kwargs = kwargs

    def run(self):



        try:

            result = self.task_func(*self.args, **self.kwargs)
            #print(result)
            self.result_signal.emit(result)

        except Exception as e:

            self.result_signal.emit(e)

        finally:
            self.finished_signal.emit()  # Send completion signal after task finishes
