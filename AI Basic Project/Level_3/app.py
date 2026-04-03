import heapq
import os
import pickle
import time
import traceback
import io
from flask import Flask, render_template, request, jsonify, send_file

# 설정: 폴더 구조
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, 'uploads')
DIRS = {
    'compressed': os.path.join(UPLOAD_BASE, 'compressed'),
    'restored': os.path.join(UPLOAD_BASE, 'restored')
}

# 필요한 디렉토리 생성
for path in DIRS.values():
    if not os.path.exists(path):
        os.makedirs(path)

# 허프만 트리의 노드 클래스
class Node:
    """허프만 트리의 각 노드를 나타내는 클래스"""
    def __init__(self, char, freq):
        self.char = char  # 문자 (내부 노드의 경우 None)
        self.freq = freq  # 빈도수
        self.left = None  # 왼쪽 자식 노드
        self.right = None  # 오른쪽 자식 노드

    def __lt__(self, other):
        """힙 정렬을 위한 비교 연산자 (빈도수 기준)"""
        return self.freq < other.freq

class HuffmanCoding:
    """허프만 코딩 압축/복원 알고리즘 구현 클래스"""
    def __init__(self):
        self.heap = []  # 우선순위 큐 (최소 힙)
        self.codes = {}  # 문자 -> 이진 코드 매핑
        self.reverse_mapping = {}  # 이진 코드 -> 문자 매핑

    def make_frequency_dict(self, text):
        """텍스트에서 각 문자의 빈도수를 계산"""
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        return freq

    def make_heap(self, frequency):
        """빈도수 딕셔너리로부터 최소 힙 생성"""
        for key in frequency:
            heapq.heappush(self.heap, Node(key, frequency[key]))

    def merge_nodes(self):
        """힙의 노드들을 병합하여 허프만 트리 구성"""
        while len(self.heap) > 1:
            # 빈도수가 가장 작은 두 노드를 꺼냄
            n1 = heapq.heappop(self.heap)
            n2 = heapq.heappop(self.heap)
            # 두 노드를 자식으로 하는 새로운 내부 노드 생성
            merged = Node(None, n1.freq + n2.freq)
            merged.left = n1
            merged.right = n2
            # 병합된 노드를 다시 힙에 삽입
            heapq.heappush(self.heap, merged)

    def make_codes(self):
        """허프만 트리를 순회하며 각 문자의 이진 코드 생성"""
        if not self.heap:
            return
        root = heapq.heappop(self.heap)
        self.root_node = root  # 시각화를 위해 루트 노드 저장
        self._make_codes_helper(root, "")

    def _make_codes_helper(self, root, current_code):
        """재귀적으로 트리를 순회하며 코드 생성 (왼쪽=0, 오른쪽=1)"""
        if root is None:
            return
        # 리프 노드(문자가 있는 노드)에 도달하면 코드 저장
        if root.char is not None:
            self.codes[root.char] = current_code
            self.reverse_mapping[current_code] = root.char
            return
        # 왼쪽 자식은 '0', 오른쪽 자식은 '1' 추가
        self._make_codes_helper(root.left, current_code + "0")
        self._make_codes_helper(root.right, current_code + "1")

    def get_encoded_text(self, text):
        """원본 텍스트를 허프만 코드로 인코딩"""
        return "".join([self.codes[char] for char in text])

    def pad_encoded_text(self, encoded_text):
        """인코딩된 텍스트를 8비트 단위로 패딩"""
        # 8의 배수가 되도록 패딩 추가
        extra_padding = 8 - len(encoded_text) % 8
        for i in range(extra_padding):
            encoded_text += "0"
        # 패딩 정보를 8비트로 저장 (복원 시 필요)
        padded_info = "{0:08b}".format(extra_padding)
        return padded_info + encoded_text

    def get_byte_array(self, padded_encoded_text):
        """패딩된 이진 문자열을 바이트 배열로 변환"""
        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            byte = padded_encoded_text[i:i+8]
            b.append(int(byte, 2))
        return b

    def get_mermaid_graph(self):
        """허프만 트리를 Mermaid 그래프 형식으로 변환 (시각화용)"""
        graph = ["graph TD"]

        def traverse(node, node_id):
            """트리를 순회하며 Mermaid 문법 생성"""
            if node is None:
                return
            # 노드 레이블 생성 (문자와 빈도수)
            label = f"'{node.char}'<br>({node.freq})" if node.char else f"{node.freq}"
            # 특수 문자 처리
            if node.char == ' ':
                label = "'SPACE'<br>(" + str(node.freq) + ")"
            if node.char == '\n':
                label = "'NEWLINE'<br>(" + str(node.freq) + ")"
            label = label.replace('"', '')
            graph.append(f'{node_id}("{label}")')
            # 왼쪽 자식 (0)
            if node.left:
                graph.append(f'{node_id} -->|0| {node_id}L')
                traverse(node.left, f"{node_id}L")
            # 오른쪽 자식 (1)
            if node.right:
                graph.append(f'{node_id} -->|1| {node_id}R')
                traverse(node.right, f"{node_id}R")

        if hasattr(self, 'root_node'):
            traverse(self.root_node, "Root")
        return "\n".join(graph)

# Flask 앱 초기화
app = Flask(__name__)

@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress_route():
    """파일 압축 엔드포인트"""
    try:
        # 파일 업로드 확인
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400

        file = request.files['file']
        # 파일 내용을 UTF-8로 디코딩
        text = file.read().decode('utf-8', errors='ignore')

        # 파일명에서 확장자 제거
        filename_no_ext = os.path.splitext(file.filename)[0]
        huffman = HuffmanCoding()
        start_time = time.time()

        # 허프만 코딩 압축 과정
        freq = huffman.make_frequency_dict(text)  # 1. 빈도수 계산
        huffman.make_heap(freq)  # 2. 힙 생성
        huffman.merge_nodes()  # 3. 허프만 트리 구성
        huffman.make_codes()  # 4. 코드 생성

        # 텍스트 인코딩 및 바이트 변환
        encoded = huffman.get_encoded_text(text)
        padded = huffman.pad_encoded_text(encoded)
        b_arr = huffman.get_byte_array(padded)

        end_time = time.time()

        # 헤더 생성 (복원에 필요한 정보 저장)
        header_data = {'codes': huffman.reverse_mapping, 'filename': file.filename}
        header = pickle.dumps(header_data)
        header_len = len(header).to_bytes(4, 'big')

        # 압축 파일 저장
        output_filename = f"compressed_{filename_no_ext}.bin"
        output_path = os.path.join(DIRS['compressed'], output_filename)

        with open(output_path, 'wb') as f:
            f.write(header_len)  # 헤더 길이 (4바이트)
            f.write(header)  # 헤더 (코드 매핑 정보)
            f.write(bytes(b_arr))  # 압축된 데이터

        # 압축 통계 계산
        original_size = len(text.encode('utf-8'))
        compressed_size = os.path.getsize(output_path)
        avg_bits = len(encoded) / len(text) if text else 0

        # 압축 파일의 16진수 미리보기 (처음 300바이트)
        with open(output_path, 'rb') as f:
            hex_dump = f.read(300).hex(' ')

        # 결과 반환
        return jsonify({
            'original_size': original_size,
            'compressed_size': compressed_size,
            'ratio': round((1 - compressed_size / original_size) * 100, 2),
            'exec_time': round(end_time - start_time, 6),
            'avg_bits': round(avg_bits, 4),
            'mermaid_graph': huffman.get_mermaid_graph(),
            'codes': huffman.codes,
            'hex_preview': hex_dump,
            'download_url': f"/download/{output_filename}"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/decompress', methods=['POST'])
def decompress_route():
    """파일 복원 엔드포인트"""
    try:
        # 파일 업로드 확인
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400

        file = request.files['file']
        start_time = time.time()

        # 파일 내용을 메모리에서 바로 읽음
        file_bytes = file.read()
        f = io.BytesIO(file_bytes)

        # 헤더 읽기 (압축 시 저장한 정보)
        header_len = int.from_bytes(f.read(4), 'big')
        header = f.read(header_len)
        header_data = pickle.loads(header)

        # 코드 매핑 정보와 원본 파일명 추출
        reverse_mapping = header_data['codes']
        original_filename = header_data.get('filename', 'restored.txt')

        # 압축된 데이터 읽기
        body = f.read()

        # 바이트를 이진 문자열로 변환
        bit_string = "".join([bin(byte)[2:].rjust(8, '0') for byte in body])

        # 패딩 정보 추출 및 제거
        if len(bit_string) >= 8:
            extra_padding = int(bit_string[:8], 2)
            bit_string = bit_string[8:]
            encoded_text = bit_string[:-extra_padding] if extra_padding > 0 else bit_string
        else:
            raise ValueError("파일 데이터 손상")

        # 이진 코드를 문자로 디코딩
        current_code = ""
        decoded_list = []
        for bit in encoded_text:
            current_code += bit
            # 현재 코드가 매핑에 존재하면 해당 문자 추가
            if current_code in reverse_mapping:
                decoded_list.append(reverse_mapping[current_code])
                current_code = ""

        restored_text = "".join(decoded_list)
        end_time = time.time()

        # 복원된 파일 저장 (다운로드용)
        restored_name = f"restored_{original_filename}"
        output_path = os.path.join(DIRS['restored'], restored_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(restored_text)

        # 결과 반환
        return jsonify({
            'success': True,
            'exec_time': round(end_time - start_time, 6),
            'text_preview': restored_text[:500] + "...",
            'download_url': f"/download/{restored_name}"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    """파일 다운로드 엔드포인트"""
    # 압축 또는 복원 폴더에서 파일 찾기
    for folder in DIRS.values():
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)