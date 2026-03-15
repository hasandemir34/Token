# Gramer Kuralları
# Kural No: (LHS, RHS Token Sayısı)
grammar = {
    1: ('E', 3),  # 1. E -> E + T  (Sağda 3 token var: E, +, T)
    2: ('E', 1),  # 2. E -> T      (Sağda 1 token var: T)
    3: ('T', 3),  # 3. T -> T * F
    4: ('T', 1),  # 4. T -> F
    5: ('F', 3),  # 5. F -> ( E )
    6: ('F', 1)   # 6. F -> id
}


# Action Tablosu
# action_table[state][token] -> 'action'
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


# Goto Tablosu
# goto_table[state][non-terminal] -> yeni_state
goto_table = {
    0: {'E': 1, 'T': 2, 'F': 3},
    4: {'E': 8, 'T': 2, 'F': 3},
    6: {'T': 9, 'F': 3},
    7: {'F': 10}
}


import sys

# Dilimizin kabul ettiği geçerli semboller (Terminaller)
VALID_TOKENS = {'id', '+', '*', '(', ')', '$'}

def read_tokens_from_file(file_path):
    """
    Belirtilen dosyayı okur, boşluklara göre ayırır ve token listesi döndürür.
    Bilinmeyen bir token ile karşılaşırsa programı durdurur.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Dosyadaki metni alıyoruz ve başındaki/sonundaki boşlukları temizliyoruz
            content = file.read().strip()
            
        # Metni boşluk (" ") karakterine göre ayırıp listeye çeviriyoruz
        tokens = content.split()
        
        # Bilinmeyen token kontrolü (Burası input9.txt'deki hatayı yakalayacak)
        for token in tokens:
            if token not in VALID_TOKENS:
                print(f"Unknown token: {token}")
                sys.exit(1) # Programı hata ile sonlandır
                
        return tokens
        
    except FileNotFoundError:
        print(f"Error: {file_path} dosyasi bulunamadi.")
        sys.exit(1)

# Test etmek için küçük bir kod (Şimdilik çalışıp çalışmadığını görmek için)





def parse(tokens):
    """
    LR Ayrıştırma algoritmasını çalıştırır ve adım adım izleme tablosunu yazdırır.
    """
    # Yığıt (stack) başlangıçta sadece 0 durumunu (state) içerir
    stack = [0]
    
    # Kalan girdiyi takip etmek için bir kopyasını alıyoruz
    input_buffer = tokens.copy()
    
    # Tablo başlıklarını yazdır (İstenilen formata uygun genişliklerde)
    print(f"{'Stack':<40} {'Input':<40} {'Action'}")
    print("-" * 104)
    
    while True:
        # Yığıtın en üstündeki durum (state) her zaman listenin en son elemanıdır
        current_state = stack[-1]
        
        # Girdideki sıradaki token (Okunacak ilk eleman)
        current_token = input_buffer[0]
        
        # Action tablosundan hamleyi bul (Eğer o hücre boşsa KeyError fırlatır, bunu hataya çevireceğiz)
        try:
            action = action_table[current_state][current_token]
        except KeyError:
            # Tabloda karşılığı yoksa Syntax Error (Sözdizimi Hatası) demektir
            print(f"\nSYNTAX ERROR at token: {current_token}")
            return False # Ayrıştırma başarısız oldu
        
        # --- Ekrana yazdırmak için mevcut durumu string'e çevir ---
        stack_str = "".join(str(item) for item in stack)
        input_str = " ".join(input_buffer)
        # -----------------------------------------------------------
        
        # 1. SHIFT (Kaydırma) İşlemi: 's' ile başlıyorsa
        if action.startswith('s'):
            next_state = int(action[1:]) # 's5' ise 5'i al
            
            # Eylemi ekrana yazdır
            print(f"{stack_str:<40} {input_str:<40} Shift {next_state}")
            
            # Token'ı ve yeni durumu yığıta ekle
            stack.append(current_token)
            stack.append(next_state)
            
            # İşlenen token'ı girdiden çıkar
            input_buffer.pop(0)
            
        # 2. REDUCE (İndirgeme) İşlemi: 'r' ile başlıyorsa
        elif action.startswith('r'):
            rule_num = int(action[1:]) # 'r6' ise 6'yı al
            lhs, rhs_length = grammar[rule_num]
            
            # Yığıttan (2 * RHS uzunluğu) kadar eleman çıkarıyoruz
            # Çünkü yığıtta her token için hem sembol hem de state tutuyoruz (örn: 'id', 5)
            for _ in range(2 * rhs_length):
                stack.pop()
                
            # Yığıtın yeni en üstündeki durumu (state) al
            top_state = stack[-1]
            
            # Goto tablosundan yeni durumu bul
            goto_state = goto_table[top_state][lhs]
            
            # Eylemi ekrana yazdır
            print(f"{stack_str:<40} {input_str:<40} Reduce {rule_num} (GOTO [{top_state}, {lhs}])")
            
            # LHS (örn: E, T, F) ve Goto tablosundan gelen yeni durumu yığıta ekle
            stack.append(lhs)
            stack.append(goto_state)
            
        # 3. ACCEPT (Kabul) İşlemi
        elif action == 'accept':
            print(f"{stack_str:<40} {input_str:<40} Accept")
            print("-" * 104)
            print("Parsing completed successfully!")
            return True # Ayrıştırma başarıyla bitti


if __name__ == "__main__":
    # Test için örnek bir girdi listesi verelim (input1.txt karşılığı)
    test_tokens = ['id', '+', 'id', '*', 'id', '$']
    parse(test_tokens)
