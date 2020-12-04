# -*- coding: utf-8 -*-
#! /usr/bin/python

# Import de divers modules et de la fenêtre
from PyQt5 import QtWidgets
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys, os, platform, socket
from infos import *
import psutil, GPUtil, math
from datetime import datetime

# Création d'une fonction de formatage de taille de données
def get_size(bytes):

    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """

    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}"
        bytes /= factor

# Création de la classe TuxInfos permettant d'exploiter la fenêtre
class TuxInfos(QtWidgets.QMainWindow):
    """Création d'une classe permettant l'exploitation de la fenêtre."""

    def __init__(self):
        super(TuxInfos, self).__init__()
        self.ui = Ui_mw_tuxinfo()
        self.ui.setupUi(self)
        self.initbouton()
        self.ui.tab_infos.setCurrentIndex(0)
        self.ui.btn_scan.clicked.connect(self.on_click)
        self.setWindowIcon(QtGui.QIcon("Tuxicon.ico"))

    def initbouton(self):

        """
        Permet de fermer la fenêtre en cliquant sur le bouton OK.
        """
        self.ui.btn_OK.clicked.connect(QApplication.instance().quit)

    def detect_config(self):

        """
        Permet de remplir les zones de saisie à l'aide des informations
        fournies par l'OS.
        """
        # Onglet machine.
        self.gestionhostname()
        self.ui.edt__typeprocesseur.setText(platform.processor())
        is_64bits = sys.maxsize > 2**32
        if is_64bits == True:
            self.ui.edt_architecture.setText("64 bits")
        else:
            self.ui.edt_architecture.setText("32 bits")
        self.ui.edt_login.setText(os.getlogin())
        self.detect_processeur()
        self.detect_ram()

        # Onglet GPU
        self.detect_nvidia()

        # Onglet système.
        self.ui.edt_nomos.setText(platform.system())
        self.ui.edt_architectureos.setText(platform.architecture()[0])
        # Gestion des numéro de version en fonction de l'OS
        if platform.system() == "Windows":
            self.ui.edt_versionmajeur.setText(str(sys.getwindowsversion().major))
            self.ui.edt_versionmineur.setText(str(sys.getwindowsversion().minor))
            self.ui.edt_buildos.setText(str(sys.getwindowsversion().build))
            self.ui.edt_editionos.setText(str(platform.win32_edition()))
        elif platform.system() == "Linux":
            self.ui.edt_versionmajeur.setText(platform.release())
            self.ui.edt_versionmineur.setText("Non Valide")
            self.ui.edt_buildos.setText("Non Valide")
            self.ui.edt_editionos.setText("Non Valide")
            self.ui.lbl_versionmajeur.setText("Version du noyau Linux :")

        # Onglet réseau.
        if platform.system() == "Windows":
            self.detect_reseauWindows()

        elif platform.system() == "Linux":
            self.detect_reseauLinux()

    def on_click(self):
        self.detect_config()

    def gestionhostname(self):

        """
        Permet le découpage du fqdn en nom + domaine dans le cas ou la machine
        est dans un domaine. Dans le cas contraire, affiche simplement le nom
        de la machine.
        """
        hostname = platform.node()
        position = hostname.find(".")
        if position == -1:
            self.ui.edt_nommachine.setText(platform.node())
            self.ui.edt_nomdomaine.setText("aucun")
            self.ui.edt_fqdn.setText("aucun")
        else:
            taille = len(hostname)
            domaine = hostname[position + 1:taille]
            self.ui.edt_nommachine.setText(hostname[0:position])
            self.ui.edt_nomdomaine.setText(domaine)
            self.ui.edt_fqdn.setText(platform.node())

    def detect_processeur(self):
        # Nombre de coeurs
        self.ui.edt_coeursphys.setText(str(psutil.cpu_count(logical=False)))
        self.ui.edt_coeurstotal.setText(str(psutil.cpu_count(logical=True)))

        # Fréquences du CPU
        cpufreq = psutil.cpu_freq()
        poucent_cpu = psutil.cpu_percent()
        self.ui.edt_freqmaxi.setText(str('{:.2f}'.format(cpufreq.max)))
        self.ui.edt_freqmini.setText(str('{:.2f}'.format(cpufreq.min)))
        self.ui.edt_freqencours.setText(str('{:.2f}'.format(cpufreq.current)))
        self.ui.pb_utilcpu.setValue(int(poucent_cpu))


    def detect_ram(self):
        # Récupération des information sur la RAM
        svmem = psutil.virtual_memory()
        self.ui.edt_tailleram.setText(str(get_size(svmem.total)))
        self.ui.edt_ramdispo.setText(str(get_size(svmem.available)))
        self.ui.edt_ramutilisee.setText(str(get_size(svmem.used)))
        self.ui.pb_pourcentageram.setValue(int(svmem.percent))

    def detect_reseauLinux(self):
        infos_reseau = psutil.net_if_addrs()
        self.ui.ptedt_macaddresse.clear()
        for nom_carte, addresses_carte in infos_reseau.items():
            for address in addresses_carte:
                if str(address.family) == 'AddressFamily.AF_INET':
                    self.ui.edt_adresseipv4.setText(address.address)
                    self.ui.edt_masquev4.setText(address.netmask)
                    self.ui.edt_broadcastv4.setText(address.broadcast)
                elif str(address.family) == 'AddressFamily.AF_INET6':
                    self.ui.edt_adresseipv6.setText(address.address)
                    self.ui.edt_masquev6.setText(address.netmask)
                    self.ui.edt_broadcastv6.setText(address.broadcast)
                elif str(address.family) == 'AddressFamily.AF_PACKET' and address.address != "00:00:00:00:00:00":
                    self.ui.ptedt_macaddresse.insertPlainText(address.address)
                    self.ui.ptedt_macaddresse.insertPlainText("\n")

    def detect_reseauWindows(self):
        print("reseau windows")
        infos_reseau = psutil.net_if_addrs()
        self.ui.ptedt_macaddresse.clear()
        for nom_carte, addresses_carte in infos_reseau.items():
            for address in addresses_carte:
                if str(address.family) == 'AddressFamily.AF_LINK':
                    self.ui.ptedt_macaddresse.insertPlainText(address.address)
                    self.ui.ptedt_macaddresse.insertPlainText("\n")

                elif str(address.family) == 'AddressFamily.AF_INET' and address.address != "127.0.0.1":
                    self.ui.edt_adresseipv4.setText(address.address)
                    self.ui.edt_masquev4.setText(address.netmask)
                    self.ui.edt_broadcastv4.setText("Inconnue")

                elif str(address.family) == 'AddressFamily.AF_INET6':
                    if address.address != "::1":
                        self.ui.edt_adresseipv6.setText(address.address)
                    self.ui.edt_masquev6.setText("Inconnue")
                    self.ui.edt_broadcastv6.setText("Inconnue")

    def detect_nvidia(self):
        gpus = GPUtil.getGPUs()
        list_gpus = []
        for gpu in gpus:
            # Identifiant du GPU
            self.ui.edt_idgpu.setText(str(gpu.id))

            self.ui.edt_uuidgpu.setText(str(gpu.uuid))

            # Nom du GPU
            self.ui.edt_nomgpu.setText(gpu.name)

            # Charge du GPU sur une progress bar
            self.ui.pb_chargegpu.setValue(int(gpu.load*100))

            # Quantité de mémoire restant
            self.ui.edt_memlibre.setText(str(gpu.memoryFree))

            # Quantité de mémoire utilisé
            self.ui.edt_memutilisee.setText(str(gpu.memoryUsed))

            # Quantité de mémoire totale.
            self.ui.edt_taillemem.setText(str(gpu.memoryTotal))

            # Température du GPU
            self.ui.edt_tempgpu.setText(str(gpu.temperature))


    def showEvent(self, event):
        self.detect_config()


if __name__ == "__main__":
    ''' Application principale '''
    app = QtWidgets.QApplication(sys.argv)
    w = TuxInfos()
    w.show()
    sys.exit(app.exec_())
