
import traceback
import cmd
import json
import os
from IPython import get_ipython
from common import DBBuilder,cprint

'''
Usage 1: WorkShell(db:dictionary,PATH:string)
Usage 2: WorkShell(builder:DBBuilder)
'''
class WorkShell(cmd.Cmd):
    # db -> node - > chunks -> <list>
    # db = { SrcFile: node }
    # node =  { chunks }
    # chunks = { DestFile : <list> }
    # <list> = [row]
    _current_node_index = 0
    _current_chunk_index = 0
    
    db = {}
    db_index_list = []
    CACHE_PATH = ''
    is_notebook = False
    

    def __init__(self, project_name:str=None,builder:DBBuilder=None):
        super(WorkShell, self).__init__()
        if project_name:
            self.init_from_project_name(project_name)
        if builder:
            self.init_from_builder(builder)
    def init_from_project_name(self,project_name:str):
        self.CACHE_PATH = project_name+'.json'
        try:
            with open(self.CACHE_PATH,'r') as r:
                self.db = json.load(r)
            self.db_index_list = list(self.db.keys())
            self.is_notebook = self.is_notebook()
            if self.is_notebook:
                cprint('Welcome to Shell, you are using Jupyter notebook','SHELL')
            else:
                cprint('Welcome to Shell, you are using None Jupyter notebook','SHELL')
        except:
            cprint('Load project json file failed','SHELL',project_name)
    def init_from_builder(self,builder:DBBuilder):
        self.CACHE_PATH = builder.get_project_name()+'.json'
        self.db = builder.get_db()
        self.db_index_list = list(self.db.keys())
        self.is_notebook = self.is_notebook()
        if self.is_notebook:
            cprint('Welcome to Shell, you are using Jupyter notebook','SHELL')
        else:
            cprint('Welcome to Shell, you are using None Jupyter notebook','SHELL')

    def is_notebook(self):
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                return True   # Jupyter notebook or qtconsole
            elif shell == 'TerminalInteractiveShell':
                return False  # Terminal running IPython
            else:
                return False  # Other type (?)
        except NameError:
            return False      # Probably standard Python interpreter

    def _clear_console(self):
        if self.is_notebook:
            from IPython.display import clear_output
            clear_output()#for ipynb
        else:
            os.system('cls')#for windows console

    def _get_code_line(self,id,N):
        current_chunk = self._get_current_chunk()
        try:
            for i in current_chunk:
                if i['#'] == id:
                    path = i['SrcFilePath']
                    with open(path,mode='r',encoding='UTF-8') as f:
                        head = [next(f) for x in range(i['Line']+N)]
                    for i in range(i['Line'],i['Line']+N):
                        print(head[i].strip().replace('\n',''))
            return 0
        except:
            print('Out of file length')
            traceback.print_exc()
            return 1
                              

    def _get_current_node(self):
        return self.db[self.db_index_list[self._current_node_index]]
    def _get_current_chunk(self):
        return self._get_current_node()[list(self._get_current_node().keys())[self._current_chunk_index]]
        
    def _set_current_node(self,node):
        self.db[self.db_index_list[self._current_node_index]] = node
        return self._get_current_node()

    def _set_reference(self,id,target_id):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] =f'As the code triggers this issue and the remediation is the same, please refer to #{str(target_id)}'
                i['Status'] = None
                i['reference'] = int(target_id)
                
    def _detach_reference(self,id):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] = None
                i['Status'] = None
                del i['reference']

    def _set_open_comment(self,id,comment):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] = comment
                i['Status'] = 'Open'
                
    def _set_fp_comment(self,id,comment):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] = comment
                i['Status'] = 'False Positive'
                
                
    def _set_pending_comment(self,id,comment):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] = comment
                i['Status'] = 'Pending'
    def _add_comment(self,id,comment):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] += comment
                
    def _remove_comment(self,id):
        current_chunk = self._get_current_chunk()
        for i in current_chunk:
            if i['#'] == id:
                i['Comment'] = ''
                i['Status'] = ''


    def _set_comment_template(self,id,type):
        current_chunk = self._get_current_chunk()
        if type.lower() == 'fp':
            for i in current_chunk:
                if i['#'] == id:
                    i['Comment'] = 'There is no logical relationship between the data flow provided by Checkmarx.'
                    i['Status'] = 'False Positive'
        elif type.lower() =='sqlformat':
            for i in current_chunk:
                if i['#'] == id:
#                     i['Comment'] = f"The application uses 'String.format' to embed untrusted params and construct sql queries, and executes queries in the function '{ExecuteScalar}' at line {508} of {Unisoft.Library/Unisoft.Net.Common/Helper/SQLHelper.cs}, which may cause sql injection attacks. Moreover, we observed that each time before executing queries, '{ExecuteScalar}' will call the function '{PrepareCommand}' at line 842 of Unisoft.Library/Unisoft.Net.Common/Helper/SQLHelper.cs to prepare sql query strings. We recommend to add sql injection prevention methods into the function '{PrepareCommand}' such as Prepared Statement, Input Validation Check, Sanitization, instead of string concatenation. "
                    i['Status'] = 'Open'
                    i['Comment'] = f"The application uses 'String.format' to embed untrusted params and construct sql queries at line {i['Line']} of {i['SrcFileName']}, which may cause sql injection attacks."
        elif type.lower() == "sql+":
            for i in current_chunk:
                if i['#'] == id:
                    i['Status'] = 'Open'
                    i['Comment'] = f"The application uses string concatenation to embed untrusted params and construct sql queries at line {i['Line']} of {i['SrcFileName']}, which may cause sql injection attacks."
        elif type.lower() == "pending":
            for i in current_chunk:
                if i['#'] == id:
                    i['Status'] = 'Pending Further Information'
                    i['Comment'] = f"Through the code snippet provided by Checkmarx, we know that the application deserializes  an object which is a FileStream read from a file at line {i['Line']} of {i['SrcFileName']}. However, we are not aware that whether the file is user controlled, thus we could not consider the status of the vulnerability to be Open."
    #edit interface
    def _edit_current_chunk(self):
        cprint('Node ' +str(self._current_node_index+1) +'/'+str(len(self.db)))
        cprint('Chunk '+str(self._current_chunk_index+1)+'/'+str(len(self.db[self.db_index_list[ self._current_node_index]])))
        current_chunk = self._get_current_chunk()
        #Print basic info of this chunk
        print(current_chunk[0]["SrcFileName"],'--->',current_chunk[0]["DestFileName"])
        #interface_dic : {key:[linked_key,code],key:[linked_key,code]}
        interface_dic = {}
#         print(current_chunk)
        for i in current_chunk:
            if 'reference' in i:
                interface_dic[int(i['reference'])][0] += ( '-' + str(i['#']))
            else:
                interface_dic[int(i['#'])] = [str(i['#']),"["+str(i['Line'])+"]"+i['SrcCode'][1], "["+str(i['DestLine'])+"]"+i['DestCode'][1]]

                
#         for key in interface_dic.keys():
        for i in current_chunk:
            if 'reference' in i:
                pass
            else:
                if i['Status'] == 'Open':
                    print("\033[32;1m [Open]",end='')
                    print('\033[1;32;43m'+interface_dic[i['#']][0]+'\033[0m',end='')
                    print("\033[32;1m"+i['Comment']+'\033[0m')
            
                    print(interface_dic[i['#']][1])
                    print(interface_dic[i['#']][2])
                elif i['Status'] == 'False Positive':
                    print("\033[33;1m [FP]",end='')
                    print('\033[1;32;43m'+interface_dic[i['#']][0]+'\033[0m',end='')
                    print("\033[33;1m"+i['Comment']+'\033[0m')
                    print(interface_dic[i['#']][1])
                    print(interface_dic[i['#']][2])
                elif i['Status'] == 'Pending Further Information':
                    print("\033[33;1m [Pending]",end='')
                    print('\033[1;32;43m'+interface_dic[i['#']][0]+'\033[0m',end='')
                    print("\033[33;1m"+i['Comment']+'\033[0m')
                    print(interface_dic[i['#']][1])
                    print(interface_dic[i['#']][2])
                else:
                    print("\033[31;1m [UnChecked]",end='')
                    print('\033[1;32;43m'+interface_dic[i['#']][0]+'\033[0m')
                    print(interface_dic[i['#']][1])
                    print(interface_dic[i['#']][2])
                          

    #Shell Commands

    def do_EOF(self, line):
        with open(self.CACHE_PATH,'w') as w:
            w.write(json.dumps(self.db,indent=4))
        print('json file is saved.')
        return True
    
    def do_duo(self,line):
        print(line.split(' '))
    
    def do_edit(self,line=None):
        if not line:
            self._clear_console()
            self._edit_current_chunk()
        else:
            try:
                args = line.split(' ')
                node_index = int(args[0]) - 1
                chunk_index = int(args[1]) - 1
                if node_index >= len(self.db) or node_index<0:
                    print('[edit] invaild node index')
                elif chunk_index >= len(self._get_current_node()) or chunk_index < 0:
                    print('[edit] invaild chunk index')
                else:
                    self._current_node_index = node_index
                    self._current_chunk_index = chunk_index
                    self._clear_console()
                    self._edit_current_chunk()
            except Exception as e:
                print('[edit] unacceptable args, usage: edit <node_index> <chunk_index>')
                traceback.print_exc()

        
    def do_nextchunk(self,line):
        self._clear_console()
        if self._current_chunk_index + 1 ==len(self._get_current_node()):
            print('This is the last chunk.')
        else:
            self._current_chunk_index +=1
            self.do_edit(None)
        
    def do_lastchunk(self,line):
        self._clear_console()
        if self._current_chunk_index == 0:
            print('This is the first chunk.')
        else:
            self._current_chunk_index -= 1
            self.do_edit(None)
        
    def do_nextnode(self,line):
        self._clear_console()
        if self._current_node_index + 1 ==len(self.db):
            print('This is the last node')
        else:
            self._current_node_index += 1
            self.do_edit(None)
            
    def do_lastnode(self,line):
        self._clear_console()
        if self._current_node_index == 0:
            print('This is the first node')
        else:
            self._current_node_index -= 1
            self.do_edit(None)
            
    def do_search(self,id):
        node_num = 0
        
        for node_key in self.db.keys():
            chunk_num = 0
            for chunk_key in self.db[node_key].keys():
                sublist = self.db[node_key][chunk_key]
                for i in sublist:
                    if i['#'] == id:
                        self.do_edit(str(node_num)+' '+str(chunk_num))
                chunk_num+=1
            node_num+=1
        
            
    def do_comment(self,line):
        if not line:
            print('[comment]: comment <id> -m <message>/ -r / -t <template>')
        else:
            try:
                args = line.split(' ')
                if '-m' in args:
                    self._set_open_comment(int(args[0]),' '.join(args[args.index('-m')+1:]))
                    self.do_edit(None)
                elif '-fp' in args:
                    self._set_fp_comment(int(args[0]),' '.join(args[args.index('-fp')+1:]))
                    self.do_edit(None)
                elif '-pending' in args:
                    self._set_pending_comment(int(args[0]),' '.join(args[args.index('-pending')+1:]))
                    self.do_edit(None)
                    
                elif '-r' in args:
                    self._remove_comment(int(args[0]))
                    self.do_edit(None)
                elif '-t' in args:
                    self._set_comment_template(int(args[0]),args[args.index('-t')+1])
                    self.do_edit(None)
                    
                elif '-a' in args:
                    self._add_comment(int(args[0]),' '.join(args[args.index('-a')+1:]))
                    self.do_edit(None)
                elif '-ref' in args:
                    self._set_reference(int(args[0]),args[args.index('-ref')+1])
                    self.do_edit(None)
                elif '-deref' in args:
                    self._detach_reference(int(args[0]))
                    self.do_edit(None)
                    
            except:
                print('[comment]: Unvalid args')
                print('[comment]: comment <id> -m <message>/-fp <message>  /-r / -t <template> <fp/sqlformat/sql+/pending> / -ref <target_id> / -deref')
                traceback.print_exc()
    def do_info(self,line):
        try:
            if not line:
                print('[comment]: info <id> <number of lines>')
            else:
                args = line.split(' ')
                self._get_code_line(int(args[0]),int(args[-1]))
        except:
            print('[info]: Unvalid args')
            traceback.print_exc()
    def do_c(self,line): self.do_comment(line)
    def do_lc(self,line): self.do_lastchunk(line)
    def do_nc(self,line): self.do_nextchunk(line)
    def do_ln(self,line): self.do_lastnode(line)
    def do_nn(self,line): self.do_nextnode(line)
    def do_e(self,line): self.do_edit(line)

        
    def do_merge(self,line):
        current_chunk = self._get_current_chunk()
        temp = {} #{line:id}
        for i in current_chunk:
            if not i['Line'] in temp:
                temp[i['Line']] = i['#']
            else:
                self._set_reference(i['#'],temp[i['Line']])
        self.do_edit(None)
        
    def do_save(self,line):
        with open(self.CACHE_PATH,'w') as w:
            w.write(json.dumps(self.db,indent=4))
        cprint('json file is saved.','SHELL',self.CACHE_PATH)

        
    def __del__(self):
        with open(self.CACHE_PATH,'w') as w:
            w.write(json.dumps(self.db,indent=4))
        cprint('json file is saved.','SHELL',self.CACHE_PATH)