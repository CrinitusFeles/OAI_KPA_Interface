from PyQt5.QtWidgets import QApplication
import sys
from oai_kpa_interface import OAI_KPA_Interface_controller

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OAI_KPA_Interface_controller()
    ex.show()
    sys.exit(app.exec_())
