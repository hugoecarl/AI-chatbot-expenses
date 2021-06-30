from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import sys
from io import StringIO
import contextlib
  
class SeleniumConf:
    def __init__(self):
        self.driver = None
        
    def start(self):
        options = Options()
        #options.binary_location = 'C:\\Users\\hugoc\\Desktop\\nenos\\chrome-win'
        #options.add_argument('--no-sandbox')
        #options.add_argument('--headless')
        #options.add_argument('--disable-dev-shm-usage')
        #options.add_argument('--disable-gpu')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        options.add_argument("user-data-dir=./")
        #options.add_argument("user-data-dir=C:\\Users\\hugoc\\Desktop\\nenos")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome('./chromedriver_armbian.exe', chrome_options=options)
        #self.driver = webdriver.Chrome('C:\\Users\\hugoc\\Desktop\\nenos\\chromedriver.exe', chrome_options=options)
        self.driver.get("https://web.whatsapp.com/")
        return self.driver
        

    def enter_chat(self, tar):
        target = tar
        x_arg = '//span[contains(@title,' + target + ')]'
        group_title = WebDriverWait(self.driver, 600).until(EC.presence_of_element_located((By.XPATH, x_arg)))
        group_title.click()
    
    def send_message(self, msg):
        string = msg
        inp_xpath = '//div[@class="_2_1wd copyable-text selectable-text"][@data-tab="6"]'
        input_box = self.driver.find_element_by_xpath(inp_xpath)
        time.sleep(1)
        input_box.send_keys(string + Keys.ENTER)


class DespesasProgram:
    def __init__(self, Selenium):
        self.selenium = Selenium
        self.driver = self.selenium.start()
        self.selenium.enter_chat('"Thing 3"')
        self.df = pd.read_csv('despesas_nenos.csv')
        self.tipo_pagamento = ['vr','va','cc','cd','din']
        self.tipo_despesa = {'n':'nosso','p':'pessoal','nosso':'nosso','pessoal':'pessoal'}
        self.tipo_categoria = ['mercado', 'ifood', 'lazer', 'outros', 'restaurante', 'conta', 'aluguel', 'casa', 'compras']
        self.message_list = None
        self.mensagem_diferente = False

    def parser_main(self,in_out, who, flag_msg):
        soup = BeautifulSoup(self.selenium.driver.page_source, "html.parser")
        self.message_list = soup.find_all("div", class_="message-"+in_out)[-5:]
        for i in self.message_list:
            message = i.find("span", class_="selectable-text")
            try:
                if message.text[0].isnumeric():
                    msg = message.text.split(',')
                    msg = [i.strip() for i in msg]
                else:
                    msg = message.text.split()
                if float(msg[0]) not in self.df[self.df['pagador'] == who]['valor'].values[-5:]:
                    if msg[2].lower() not in self.tipo_pagamento or msg[3].lower() not in self.tipo_despesa or msg[1].lower() not in self.tipo_categoria:
                        self.selenium.send_message("Nome grupos, tipo de pagamento ou despesa pessoal/nosso errado!")
                        for i in range(4):
                            self.selenium.send_message("Espere " + str(3-i))  
                        self.selenium.send_message("Pode tentar de novo!")                 
                        raise 
                    if len(self.df) == 0:
                        self.df.loc[0] = [0, who, float(msg[0]), msg[1], datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), msg[2].lower(), self.tipo_despesa[msg[3]], msg[4]]
                        self.selenium.send_message("Adicionado :)!")
                    else:
                        self.df.loc[len(self.df)] = [self.df.iloc[-1, 0]+1, who, float(msg[0]), msg[1], datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), msg[2].lower(), self.tipo_despesa[msg[3]], msg[4]]
                        self.selenium.send_message("Adicionado :)!")
            except:
                pass
        if msg == flag_msg:
            return flag_msg
        #Avisa 0 msgens nena
        if not self.message_list:
            self.selenium.send_message('zero mensagens de' + who)
        print('-----------------------------------------------------------------------------------')
        print(self.df)
        self.cancela(msg)
        self.delete_by_idx(msg)
        self.mostrar_infos(msg)
        self.help(msg)
        self.run_python_commands(msg)
        self.df_to_csv()
        return msg

    def cancela(self, msg):
        if msg[0][0:7].lower() == 'cancela':
            try:
                if float(self.message_list[-2].find("span", class_="selectable-text").text.split()[0]) == self.df.iloc[-1,2]:
                    self.selenium.send_message("Deletado: Despesa-"+self.df.iloc[-1,8]+", Valor-"+str(self.df.iloc[-1,2]))
                    self.df = self.df[:-1]
                else:
                    self.selenium.send_message("Falha ao deletar: Despesa-"+self.df.iloc[-1,8]+", Valor-"+str(self.df.iloc[-1,2]))
                    self.selenium.send_message("Tenta pelo id bb")
            except:
                self.selenium.send_message("Erro ao usar o comando :(!")
            
    def delete_by_idx(self, msg):
        if msg[0][0:3].lower() == 'del':
            try:
                self.df = self.df[self.df['id'] != int(msg[1])]
                self.selenium.send_message("Deletando...")
                for i in range(3):
                    self.selenium.send_message(".")
                self.selenium.send_message("Ok")
            except:
                self.selenium.send_message("Formato Mensagem errado")
    
    def mostrar_infos(self, msg):
        if msg[0][0:6].lower() == 'mostra':
            try:
                #Mostra baseado na categoria
                if msg[1].lower() == 'categoria':
                    #Mostra de todos a soma do valor, numero de vezes e nome da categoria
                    if len(msg) == 2:
                        for i in range(len(self.df.groupby(by='categoria').sum())):
                            nome = self.df.groupby(by='categoria').sum().index[i]
                            valor = self.df.groupby(by='categoria')['valor'].sum().iloc[i]
                            n_vezes = self.df.groupby(by='categoria')['id'].count().iloc[i]
                            self.selenium.send_message("Nome: "+nome+", Número de Vezes: "+str(n_vezes)+", Valor Total: "+str(valor))
                    #Mostra infos do terceiro input
                    else:
                        valor = self.df.groupby(by='categoria')['valor'].sum().loc[' '.join(msg[2:])]
                        n_vezes = self.df.groupby(by='categoria')['valor'].count().loc[' '.join(msg[2:])]
                        self.selenium.send_message("Número de Vezes: "+str(n_vezes)+", Valor Total: "+str(valor))
                elif msg[1].lower() == 'data':
                        data_format = msg[2].split('/')
                        data_format[0], data_format[2] = data_format[2], data_format[0]
                        valor = self.df.groupby(by='data')['valor'].sum().loc['-'.join(data_format)]
                        n_vezes = self.df.groupby(by='data')['valor'].count().loc['-'.join(data_format)]
                        self.selenium.send_message("Número de Compras: "+str(n_vezes)+", Valor Total: "+str(valor))
                #Mostra n ultimos no df baseado no segundo input
                else:
                    for i in range(1, int(msg[1])+1):
                        self.selenium.send_message("Id - "+str(self.df.iloc[-i,0])+ ", Categoria - "+self.df.iloc[-i,3]+", Valor - "+str(self.df.iloc[-i,2]))
            except:
                self.selenium.send_message("Formato Mensagem errado")

    def help(self, msg):
        if msg[0].lower() == 'help':
            self.selenium.send_message('Tipos de pagamento:' + str(self.tipo_pagamento))
            self.selenium.send_message('Todas as categorias:' + str(self.tipo_categoria))
            self.selenium.send_message('Formato para adicionar novos campos: valor,categoria,tipo_pagamento,nosso_pessoal,comentarios')

    def run_python_commands(self, msg):
            @contextlib.contextmanager
            def stdoutIO(stdout=None):
                old = sys.stdout
                if stdout is None:
                    stdout = StringIO()
                sys.stdout = stdout
                yield stdout
                sys.stdout = old
            try:
                if msg[0].lower() == 'run':
                    with stdoutIO() as s:
                        exec(' '.join(msg[1:]).replace('”','"').replace('“', '"'))
                    self.selenium.send_message(s.getvalue())
            except Exception as e:
                self.selenium.send_message(str(e))
    
    def df_to_csv(self):
        self.df.to_csv("despesas_nenos.csv", index=False)

    def get_driver(self):
        return self.driver

    
if __name__=="__main__":
    break_code = 0
    msg_nena = None
    msg_neno = None
    selenium = SeleniumConf()
    despesas_program = DespesasProgram(selenium)    
    while True:
        try:
            time.sleep(5)
            msg_neno = despesas_program.parser_main("out", "Neno", None)
            time.sleep(5)
            msg_nena = despesas_program.parser_main("in", "Nena", msg_nena)
        except Exception as e:
            despesas_program.get_driver().quit()
            time.sleep(10)
            selenium = SeleniumConf()
            despesas_program = DespesasProgram(selenium)
            break_code += 1
            if break_code == 1:
                print('entro')
                despesas_program.get_driver().quit()
                with open("error.txt", "a") as f:
                    f.write(str(e) + '\n')
                    f.close()
                sys.exit()
