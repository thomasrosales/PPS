#!/usr/bin/python

#######################################################
## ftp client of the Facultad de Informatica
#######################################################
## Author: Rosales, Tomas
## Copyright: Copyright 2018, MFV
## Version: 3.0 Release
## Mmaintainer: Facultad de Informatica
## Email: trosales@linti.unlp.edu.ar
## Status: production
#######################################################

import ftplib
from ftplib import FTP 
from ftplib import error_perm
import sys
import os
import time


class ftp_client():
    '''
    ftp client.

    Send files to the FTP server.

    '''
    connection = None

    def __get_connection(self):
        if self.connection == None:
            ftp = FTP('')
            ftp.connect('163.10.20.3') #default port
            ftp.login('inversores','inversores2020')
            ftp.set_pasv(False)
            self.connection = ftp      
        return self.connection

    def upload_file(self, filename):
        ftp = self.__get_connection()
        #ruta relativa del archivo pc cliente
        filename = '/home/pi/inverter_data/configuration-sirio.cfg'
        ftp.storbinary('STOR '+ filename, open(filename, 'rb'))
        ftp.quit()

    def upload_directory(self, path):
        ftp = self.__get_connection()
        print  path
        try: 
            files = os.listdir(path)
            os.chdir(path)
            for f in files:
                dir_file_list = []
                ftp.retrlines('NLST',dir_file_list.append)
                if os.path.isfile(path + '/' + f):
                    if not f in dir_file_list:
                        ftp.storbinary('STOR ' + f, open(f, 'rb'))
                elif os.path.isdir(path + '/' + f):
                    if not f in dir_file_list:
                        ftp.mkd(f)
                    ftp.cwd(f)
                    self.upload_directory(path + '/' + f)
            ftp.cwd('..')
            os.chdir('..')
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print 'Error:', e


    def download_file(self, filename):
        ftp = self.__get_connection()
        #replace with your file in the directory ('directory_name')
        filename = 'testfile.txt' 
        localfile = open(filename, 'wb')
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
        ftp.quit()
        localfile.close()

# MAIN
if __name__ == "__main__":

    cli = ftp_client()
    path = "/home/pi/inverter_data"
    try:
        cli.upload_directory(path)
    except Exception as detail:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print 'Error:', detail
    
