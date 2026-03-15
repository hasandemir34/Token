import sys
import os

# --- 1. VERİ YAPILARI (GRAMER VE TABLOLAR) ---
grammar = {
    1: ('E', 3), 
    2: ('E', 1), 
    3: ('T', 3), 
    4: ('T', 1), 
    5: ('F', 3), 
    6: ('F', 1)  
}

action_table = {
    0: {'id': 's5', '(': 's4'},
    1: {'+': 's6', '$': 'accept'},
    2: {'+': 'r2', '*': 's7', ')': 'r2', '$': 'r2'},
    3: {'+': 'r4', '*': 'r4', ')': 'r4', '$': 'r4'},
    4: {'id': 's5', '(': 's4'},
    5: {'+': 'r6', '*': 'r6', ')': 'r6', '$': 'r6'},
    6: {'id': 's5', '(': 's4'},
    7: {'id': 's5', '(': 's4'},
    8: {'+': 's6', ')': 's11'},
    9: {'+': 'r1', '*': 's7', ')': 'r1', '$': 'r1'},
    10: {'+': 'r3', '*': 'r3', ')': 'r3', '$': 'r3'},
    11: {'+': 'r5', '*': 'r5', ')': 'r5', '$': 'r5'}
}

goto_table = {
    0: {'E': 1, 'T': 2, 'F': 3},
    4: {'E': 8, 'T': 2, 'F': 3},
    6: {'T': 9, 'F': 3},
    7: {'F': 10}
}

VALID_TOKENS = {'id', '+', '*', '(', ')', '$'}

# --- 2. AĞAÇ (PARSE TREE) İÇİN DÜĞÜM SINIFI ---
class Node:
    def __init__(self, value):
        self.value = value
        self.children = []

def print_parse_tree(node, current_path=""):
    """ Ağacı /E/T/F şeklinde derinlik öncelikli (DFS) tarayarak yazdırır """
    path = current_path + "/" + node.value
    print(path)
    for child in node.children:
        print_parse_tree(child, path)

# --- 3. GİRDİ OKUMA ---
def read_tokens_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        return content.split()
    except FileNotFoundError:
        return None

# --- 4. LR AYRIŞTIRICI MANTIĞI ---
def parse(tokens):
    stack = [0]
    input_buffer = tokens.copy()
    tree_stack = [] # Ağaç düğümlerini tutacağımız yığıt
    
    print(f"{'Stack':<40} {'Input':<40} {'Action'}")
    print("-" * 104)
    
    while True:
        current_state = stack[-1]
        current_token = input_buffer[0]
        
        # input9.txt içindeki '-' gibi bilinmeyen token kontrolü
        if current_token not in VALID_TOKENS:
            print(f"Unknown token: {current_token}")
            return False
            
        try:
            action = action_table[current_state][current_token]
        except KeyError:
            # Syntax Error durumu (input7.txt)
            print("-" * 104)
            print("Parse tree:")
            if tree_stack:
                print_parse_tree(tree_stack[-1])
            return False
        
        stack_str = "".join(str(item) for item in stack)
        input_str = " ".join(input_buffer)
        
        if action.startswith('s'):
            next_state = int(action[1:])
            print(f"{stack_str:<40} {input_str:<40} Shift {next_state}")
            
            stack.append(current_token)
            stack.append(next_state)
            
            # Ağaç için: Yeni okunan terminali yığıta düğüm olarak at
            tree_stack.append(Node(current_token))
            
            input_buffer.pop(0)
            
        elif action.startswith('r'):
            rule_num = int(action[1:])
            lhs, rhs_length = grammar[rule_num]
            
            for _ in range(2 * rhs_length):
                stack.pop()
                
            top_state = stack[-1]
            goto_state = goto_table[top_state][lhs]
            
            print(f"{stack_str:<40} {input_str:<40} Reduce {rule_num} (GOTO [{top_state}, {lhs}])")
            
            stack.append(lhs)
            stack.append(goto_state)
            
            # Ağaç için: Reduce edildiğinde sağ taraftaki elemanları alıp anne düğüme (LHS) bağla
            children = []
            for _ in range(rhs_length):
                children.append(tree_stack.pop())
            children.reverse() # LIFO olduğu için sırayı düzeltiyoruz
            
            parent_node = Node(lhs)
            parent_node.children = children
            tree_stack.append(parent_node)
            
        elif action == 'accept':
            # Başarılı bittiğinde çizgiyi çekip ağacı en tepeden yazdırıyoruz
            print("-" * 104)
            print("Parse tree:")
            print_parse_tree(tree_stack[0])
            return True

# --- 5. ANA AKIŞ VE OTOMASYON (TÜM DOSYALARI ÇIKARMA) ---
if __name__ == "__main__":
    print("LR Parser Çalıştırılıyor...\n")
    
    # 1'den 9'a kadar olan girdi dosyaları
    for i in range(1, 10):
        # Eğer dosyaların TestCases isimli bir klasördeyse aşağıdaki yolu değiştirebilirsin
        input_file = f"input{i}.txt"  
        output_file = f"output{i}.txt"
        
        tokens = read_tokens_from_file(input_file)
            
        if tokens is None:
            print(f"Uyarı: {input_file} bulunamadı, diğer dosyaya geçiliyor.")
            continue
            
        print(f"İşleniyor: {input_file} -> {output_file} olarak kaydedildi.")
        
        # Ekran çıktılarını geçici olarak .txt dosyasına yönlendiriyoruz
        original_stdout = sys.stdout
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                sys.stdout = f
                parse(tokens)
        finally:
            # Yönlendirmeyi tekrar eski haline (Terminale) alıyoruz
            sys.stdout = original_stdout
            
    print("\nTüm dosyalar başarıyla oluşturuldu! Projen teslim için hazır.")