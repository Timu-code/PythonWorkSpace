import os
import re
import platform

class Colors:
    '''콘솔 출력을 위한 ANSI 색상 코드 클래스'''
    BORDER = '\033[96m'       # 테두리
    TITLE = '\033[97m'        # 제목/포인트
    INFO = '\033[97m'         # 정보 텍스트
    PROMPT = '\033[96m'       # 입력 프롬프트
    
    # 메뉴 항목별 색상
    MENU_DEFAULT = '\033[92m' # 메뉴 1
    MENU_OPTION = '\033[96m'  # 메뉴 2
    MENU_UNIQUE = '\033[95m'  # 메뉴 3
    MENU_EXIT = '\033[91m'    # 메뉴 4
    
    # 상태/결과 색상
    RESULT = '\033[92m'       # 결과 텍스트
    SUCCESS = '\033[92m'      # 성공 메시지
    ERROR = '\033[91m'        # 에러 메시지
    
    # 텍스트 스타일
    ENDC = '\033[0m'          # 텍스트 색상 초기화
    BOLD = '\033[1m'          # 텍스트 굵게
    UNDERLINE = '\033[4m'     # 텍스트 밑줄

def clear_screen() -> None:
    '''운영체제에 맞게 콘솔 화면을 지우는 함수'''
    if platform.system() == 'Windows': # 윈도우 운영체제인 경우
        os.system('cls')
        
    else: # 리눅스, 맥 운영체제인 경우
        os.system('clear')

def get_display_width(s: str) -> int:
    '''
    터미널에 출력될 때의 문자열 시각적 너비를 계산하는 함수
    ANSI 이스케이프 코드는 너비 계산에서 제외하고,
    한글/전각 문자는 너비 2, 그 외는 1로 계산
    
    Args:
        s (str): 너비를 계산할 문자열
        
    Returns:
        int: 계산된 시각적 너비
    '''
    # ANSI 이스케이프 코드 제거
    plain_text = re.sub(r'\033\[[0-9;]*m', '', s)
    
    width = 0
    
    # 각 문자의 너비를 계산
    for char in plain_text:
        # 한글, 일본어, 전각 문자 등 너비가 2인 문자 범위
        if ('\uac00' <= char <= '\ud7a3') or \
           ('\u3040' <= char <= '\u30ff') or \
           ('\uff00' <= char <= '\uffef'):
            width += 2  # 전각 문자는 너비 2
            
        else:
            width += 1  # 반각 문자는 너비 1
            
    return width

# 지원하는 문자 집합 정의 (시작문자, 끝문자, 문자개수)
CHAR_SETS = [
    ('a', 'z', 26),      # 영어 소문자
    ('A', 'Z', 26),      # 영어 대문자
    ('가', '힣', 11172), # 한글
    ('ぁ', 'ん', 83),    # 히라가나
    ('ァ', 'ヶ', 86)     # 가타카나
]

def caesar_cipher(text: str, shift: int, decrypt: bool = False) -> str:
    '''
    카이사르 암호를 사용하여 문자열을 암호화 또는 복호화하는 함수
    
    Args:
        text (str): 암호화/복호화할 문자열
        shift (int): 이동할 문자 수
        decrypt (bool): True면 복호화, False면 암호화
        
    Returns:
        str: 암호화/복호화된 문자열
    '''
    # 복호화인 경우 shift 값을 음수로 변경
    if decrypt:
        shift = -shift

    result = ''
    
    # 각 문자에 대해 암호화/복호화 수행
    for char in text:
        is_processed = False
        
        # 지원하는 문자 집합에서 해당 문자 찾기
        for start_char, end_char, count in CHAR_SETS:
            if start_char <= char <= end_char:
                base = ord(start_char)  # 기준 문자의 ASCII 값
                # 문자를 shift만큼 이동 (순환)
                new_index = (ord(char) - base + shift) % count
                result += chr(base + new_index)
                
                is_processed = True
                break
        
        # 지원하지 않는 문자는 그대로 유지
        if not is_processed:
            result += char
            
    return result

def vigenere_cipher(text: str, keyword: str, decrypt: bool = False) -> str:
    '''
    비즈네르 암호를 사용하여 문자열을 암호화 또는 복호화하는 함수
    
    Args:
        text (str): 암호화/복호화할 문자열
        keyword (str): 암호화에 사용할 키워드 (영어만 지원)
        decrypt (bool): True면 복호화, False면 암호화
        
    Returns:
        str: 암호화/복호화된 문자열 또는 에러 메시지
    '''
    # 키워드에서 영어 알파벳만 추출하여 shift 값으로 변환
    keyword_shifts = [ord(k.lower()) - ord('a') for k in keyword if 'a' <= k.lower() <= 'z']
    
    # 키워드에 영어 알파벳이 없는 경우 에러 반환
    if not keyword_shifts:
        return f'{Colors.ERROR}키워드는 영어 알파벳을 포함해야 합니다.{Colors.ENDC}'

    result = ''
    key_index = 0  # 키워드 인덱스
    
    # 각 문자에 대해 암호화/복호화 수행
    for char in text:
        is_processed = False
        # 현재 키워드 문자에 해당하는 shift 값
        shift = keyword_shifts[key_index % len(keyword_shifts)]
        
        # 복호화인 경우 shift 값을 음수로 변경
        if decrypt:
            shift = -shift

        # 지원하는 문자 집합에서 해당 문자 찾기
        for start_char, end_char, count in CHAR_SETS:
            if start_char <= char <= end_char:
                base = ord(start_char)  # 기준 문자의 ASCII 값
                # 문자를 shift만큼 이동 (순환)
                new_index = (ord(char) - base + shift) % count
                result += chr(base + new_index)
                
                key_index += 1  # 다음 키워드 문자로 이동
                is_processed = True
                break
        
        # 지원하지 않는 문자는 그대로 유지 (키워드 인덱스는 증가하지 않음)
        if not is_processed:
            result += char
    
    return result

def print_main_menu(shift_value: int) -> None:
    '''
    메인 메뉴를 출력하는 함수
    
    Args:
        shift_value (int): 현재 카이사르 암호 키 값
    '''
    width = 42  # 메뉴 박스의 너비
    title = 'Cipher Crypter'
    
    # 제목 라인 생성
    title_line_content = f'{Colors.BOLD}{Colors.TITLE}{title}{Colors.ENDC}'
    title_width = get_display_width(title_line_content)
    padding_left = (width - title_width) // 2
    padding_right = width - title_width - padding_left
    
    def create_centered_line(content: str = '') -> str:
        '''
        중앙 정렬된 라인을 생성하는 내부 함수
        
        Args:
            content (str): 라인에 표시할 내용
            
        Returns:
            str: 중앙 정렬된 라인 문자열
        '''
        colored_content = content + Colors.ENDC
        content_width = get_display_width(content)
        
        # 빈 라인인 경우
        if content == '':
            return f'{Colors.BORDER}║{" " * width}{Colors.BORDER}║{Colors.ENDC}'

        # 내용이 있는 라인인 경우 중앙 정렬
        padding_total = width - content_width
        padding_left_spaces = ' ' * (padding_total // 2)
        padding_right_spaces = ' ' * (padding_total - (padding_total // 2))
        
        return f'{Colors.BORDER}║{padding_left_spaces}{colored_content}{padding_right_spaces}{Colors.BORDER}║{Colors.ENDC}'

    # 메뉴 박스 상단 테두리
    print(f'{Colors.BORDER}╔{"═" * width}╗{Colors.ENDC}')
    # 제목 라인
    print(f'{Colors.BORDER}║{" " * padding_left}{title_line_content}{" " * padding_right}{Colors.BORDER}║{Colors.ENDC}')
    # 구분선
    print(f'{Colors.BORDER}╠{"═" * width}╣{Colors.ENDC}')
    # 빈 라인
    print(create_centered_line())
    
    # 메뉴 항목들
    menu1 = f'{Colors.MENU_DEFAULT}1. 카이사르 암호 (단일 키)'
    menu2 = f'{Colors.MENU_OPTION}2. 카이사르 암호 키 변경'
    menu3 = f'{Colors.BOLD}{Colors.MENU_UNIQUE}3. 비즈네르 암호 (다중 키)'
    menu4 = f'{Colors.MENU_EXIT}4. 종료'
    print(create_centered_line(menu1))
    print(create_centered_line(menu2))
    print(create_centered_line(menu3))
    print(create_centered_line(menu4))
    
    # 빈 라인
    print(create_centered_line())
    # 구분선
    print(f'{Colors.BORDER}╠{"═" * width}╣{Colors.ENDC}')
    
    # 정보 라인들
    info1 = f'{Colors.INFO}카이사르 암호 키: {Colors.BOLD}{shift_value}'
    info2 = f'{Colors.INFO}지원: 한국어·영어·일본어'
    print(create_centered_line(info1))
    print(create_centered_line(info2))
    
    # 메뉴 박스 하단 테두리
    print(f'{Colors.BORDER}╚{"═" * width}╝{Colors.ENDC}')

def main() -> None:
    '''메인 로직을 실행하는 함수'''
    shift = 3  # 기본 카이사르 암호 키 값

    # 메인 루프
    while True:
        # 화면 지우고 메뉴 출력
        clear_screen()
        print_main_menu(shift)
        choice = input(f'\n{Colors.BOLD}{Colors.PROMPT}메뉴 선택 ▶ {Colors.ENDC}')

        clear_screen()

        # 메뉴 1: 카이사르 암호
        if choice == '1':
            print(f'{Colors.BOLD}{Colors.TITLE}--- 카이사르 암호 ---{Colors.ENDC}\n')
            input_string = input(f'{Colors.PROMPT}입력 문자열: {Colors.ENDC}')
            
            # 암호화 및 복호화 수행
            encrypted = caesar_cipher(input_string, shift)
            decrypted = caesar_cipher(encrypted, shift, decrypt=True)
            
            # 결과 출력
            print('\n' + '─' * 40)
            print(f'{Colors.MENU_DEFAULT}암호 문자열: {Colors.BOLD}{Colors.RESULT}{encrypted}{Colors.ENDC}')
            print(f'{Colors.MENU_DEFAULT}복원 문자열: {Colors.BOLD}{Colors.RESULT}{decrypted}{Colors.ENDC}')
            print('─' * 40)
            input(f'\n{Colors.MENU_OPTION}메인 메뉴로 돌아가려면 Enter 키를 누르세요...{Colors.ENDC}')

        # 메뉴 2: 카이사르 암호 키 변경
        elif choice == '2':
            print(f'{Colors.BOLD}{Colors.TITLE}--- 카이사르 암호 키 변경 ---{Colors.ENDC}\n')
            
            # 새로운 키 입력 받기 (유효성 검사 포함)
            while True:
                try:
                    new_shift_str = input(f'{Colors.PROMPT}새로운 키(숫자)를 입력하세요 (현재: {shift}): {Colors.ENDC}')
                    if not new_shift_str: continue  # 빈 입력인 경우 다시 입력 받기
                    shift = int(new_shift_str)  # 문자열을 정수로 변환
                    print(f'\n{Colors.SUCCESS}✔ 카이사르 암호 키가 {Colors.BOLD}{shift}{Colors.ENDC}{Colors.SUCCESS}(으)로 변경되었습니다.{Colors.ENDC}')
                    break
                
                except ValueError:  # 숫자가 아닌 값이 입력된 경우
                    print(f'{Colors.ERROR}✖ 잘못된 입력입니다. 숫자를 입력해주세요.{Colors.ENDC}')
                    
            input(f'\n{Colors.MENU_OPTION}메인 메뉴로 돌아가려면 Enter 키를 누르세요...{Colors.ENDC}')

        # 메뉴 3: 비즈네르 암호
        elif choice == '3':
            print(f'{Colors.BOLD}{Colors.TITLE}--- 비즈네르 암호 ---{Colors.ENDC}\n')
            keyword = input(f'{Colors.PROMPT}사용할 키워드(영어)를 입력하세요: {Colors.ENDC}')
            input_string = input(f'{Colors.PROMPT}입력 문자열: {Colors.ENDC}')
            
            # 암호화 및 복호화 수행
            encrypted = vigenere_cipher(input_string, keyword)
            decrypted = vigenere_cipher(encrypted, keyword, decrypt=True)

            # 결과 출력
            print('\n' + '─' * 40)
            print(f'{Colors.MENU_DEFAULT}암호 문자열: {Colors.BOLD}{Colors.RESULT}{encrypted}{Colors.ENDC}')
            print(f'{Colors.MENU_DEFAULT}복원 문자열: {Colors.BOLD}{Colors.RESULT}{decrypted}{Colors.ENDC}')
            print('─' * 40)
            input(f'\n{Colors.MENU_OPTION}메인 메뉴로 돌아가려면 Enter 키를 누르세요...{Colors.ENDC}')

        # 메뉴 4: 프로그램 종료
        elif choice == '4':
            print(f'{Colors.BOLD}{Colors.ERROR}프로그램을 종료합니다.{Colors.ENDC}')
            break
            
        # 잘못된 메뉴 선택
        else:
            print(f'{Colors.ERROR}✖ 잘못된 선택입니다. 메뉴에서 다시 선택해주세요.{Colors.ENDC}')
            input(f'\n{Colors.MENU_OPTION}메인 메뉴로 돌아가려면 Enter 키를 누르세요...{Colors.ENDC}')

if __name__ == '__main__':
    main()