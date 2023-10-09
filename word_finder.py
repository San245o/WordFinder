import mysql.connector as sql
from collections import Counter #built in
from tabulate import tabulate #pip install tabulate
import time #built in
from tkinter import filedialog as fd #pip install tk
import tkinter as tk
import csv
from itertools import groupby

class FindWord:
    def __init__(self):
        self.sql_pass = None
        self.file_not_found = True
        self.wrong_pwd = True
        self.auth = None
        self.word_list = None
        self.file = None
        self.popular = {}
        self.db = False
        self.text = False
        self.records = []
        root = tk.Tk()
        root.withdraw()

        file_auth_key = "auth:gAAAAABk_d3TUybVVg_uW-fJ8UeKoFVCS2apND_LdAq2lb5YiLJuDHdjLz6lxvXyrxjhqSKhdkzqs0vuOfzYDFKAGR18msM6Cg=="
        try:
            self.adr = fd.askopenfilename(title='Open Dataset file',filetypes=[('Text files','*.txt')])
            if not self.adr:
                exit()
            with open (self.adr,'r') as self.file:
                self.word_list = ((self.file.read()).split('\n'))
                
            while self.file_not_found:
                    if self.word_list[0] == file_auth_key:   #authentication of correct file
                        self.file_not_found = False
                        break
                    else:
                        print('File does not seem to have a valid auth key.')
                        break
        except FileNotFoundError as e:
            print("File adress seems to be incorrect",e)

        try:
            with  open('popular.csv','r') as self.popular_csv:
                self.reader = csv.reader(self.popular_csv)
                for i in self.reader:
                    if i:
                        i[1] = int(i[1])
                        self.records.append(i)
        except:
            f = open('popular.csv','w')
            f.close()
        print("\nSetup Succesful, You can continue with the program \n")

    def WordExtractor(self,array):
        self.array = array
        msg = input("Enter the word[replace missing letters with '-']: ").lower()
        start = time.time()

        if msg == '':
            ch = (input("\nExit?[yes/no]: ")).lower()
            if ch == 'yes':
                self.file.close()
                exit()
            else:
                if self.text:
                    self.TextParser()  
                else: 
                    self.DatabaseParser()

        lst = list(msg)
        rmsg = msg.replace('-','')  
        rst = list(rmsg)
        ans = []
        for word in self.array:
            if len(word) == len(msg) and set(rmsg).issubset(set(word)):
                for a in range(len(lst)):
                    if lst[a] == word[a]: 
                        ans.append(word)

        c_ans = Counter(sorted(list(ans))).most_common()        
        f_ans = [[i[0]] for i in c_ans if i[1] == len(rmsg)]

        for i in range(len(f_ans)):
            f_ans[i].insert(0,i+1)

        if f_ans == []:
            print("no words were found, Please re enter correctly")
            if self.text:
                self.TextParser()
            if self.db:
                self.DatabaseParser()

        end = time.time()
        time_taken = round(end - start,2)   

        print(f'{len(f_ans)} results match out of {len(self.array)} ({time_taken*100} ms)')  
        print(tabulate(f_ans,headers=['Index','Possible Words'],tablefmt='fancy_grid'))
        search = int(input("which word were you looking for [enter the number] : "))

        while search > len(f_ans):
            print("Word out of range, Retry")
            search = int(input("which word were you looking for [enter the number] : "))
        
        word = ''.join([i[1] for i in f_ans if i[0] == search])

        found = False
        for record in self.records:
            if record[0] == word:
                record[1] = int(record[1]) + 1
                found = True
                break
        if not found:
            self.records.append([word, 1])

        with open('popular.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(self.records)

        retry = input("try again[y/n]: ")
        if retry == 'y':
            if self.text:
                self.TextParser()
            elif self.db:
                self.DatabaseParser()
        else:
            again = int(input("Would you like to\n1.Exit the program\n2.Try another functionality? : \n"))
            if again ==  1:
                exit()
            elif again == 2:
                self.db = False
                self.text = False
                return 

    def TextParser(self):
        self.text = True
        print("This is what peak performance looks like")
        self.WordExtractor(self.word_list)

    def Popularity_check(self):
        if self.records == []:
            print('\n----Insert Records First----\n')
        else:
            print('\n\t  Top 10 Most Searched Words\n')
            print(tabulate(sorted(self.records,reverse=True,key=lambda x: x[1]),headers=['Word','Count'],tablefmt='fancy_grid'))   
            print("\n")

    def UnScramble(self):
        word = input("Enter the word to unscramble it: ")
        filtered_words = [msg for msg in self.word_list if set(word) == set(msg)]
        length_to_words = {}
        for msg in filtered_words:
            length = len(msg)
            if length in length_to_words:
                length_to_words[length].append(msg)
            else:
                length_to_words[length] = [msg]
        max_num_words = max(len(words) for words in length_to_words.values())
        transposed_data = []
        for length, words in length_to_words.items():
            words += ['-' for _ in range(max_num_words - len(words))]
            transposed_data.append([f"{length} letters"] + words)
        headers = ['No.'] + [f"Word {i+1}" for i in range(max_num_words)]
        print(tabulate(transposed_data, headers=headers, tablefmt='fancy_grid', missingval='-'))

    def DatabaseParser(self):
        self.db = True
        self.sql_pass = input("Enter your mysql password: ")

        try:
            self.auth = sql.connect(user = 'root', password = self.sql_pass)
            if self.auth.is_connected():
                self.wrong_pwd = False
                
            cursor = self.auth.cursor()
            cursor.execute('CREATE DATABASE IF NOT EXISTS WORD_DATASET')
            cursor.execute('USE WORD_DATASET')
            cursor.execute('create table dataset(words varchar(200));')           

        except:
            pass
        
        try:
            self.auth = sql.connect(user = 'root', password = self.sql_pass,database = 'word_dataset')
            self.cursor = self.auth.cursor()
        except:
            print("The password seems to be incorrect, pls try again")
            import word_finder

        count = 1
        begin = time.time()
        batch_size = 10000
        self.cursor.execute('SELECT * FROM DATASET;')
        self.record = self.cursor.fetchall()

        if len(self.record) == len(self.word_list)-1:
                print("Database exists, all criterias matched ")
                array = [i[0] for i in self.record]
                self.WordExtractor(array)
        else:
            try:
                print("Inserting records into the database, this should take a few seconds")
                for i in range(1, len(self.word_list), batch_size):
                    batch = self.word_list[i:i + batch_size]
                    values = [(word,) for word in batch]
                    insert_query = "INSERT INTO dataset VALUES (%s)"

                    self.cursor.executemany(insert_query,values)
                    self.cursor.execute('SELECT COUNT(*) FROM DATASET')
                    completed = self.cursor.fetchone()
                    print(f"{round((completed[0] / len(self.word_list)) * 100, 2)}% completed",end='\r', flush=True)
                    self.auth.commit()

                end = time.time()
                print(f'Completed in {(int(end - begin)) } seconds.')

            except:
                print("There seems to be an issue with the connectivity, Retrying again...")

            self.DatabaseParser()

Instance = FindWord()

while True:
    print(f"Searching 370k+ words to help you!")
    ch = input('1. Find word through txt file\n2. Find word through mysql database\n3. Display searched words\n4. Unscramble Words\n5. Exit\nEnter your choice: ')
    if ch == '1':
        Instance.TextParser()
    elif ch == '2':
        Instance.DatabaseParser()
    elif ch == '3':
        Instance.Popularity_check()
    elif ch == '4':
        Instance.UnScramble()
    else:
        exit()

