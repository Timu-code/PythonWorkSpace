import re
from collections import defaultdict
from flask import Flask, render_template, request, jsonify
from transformers import pipeline

ner_pipeline = pipeline("ner", model="dslim/distilbert-NER", aggregation_strategy="simple")

class TextIndexer:
    """텍스트 파일을 분석하여 단어 인덱스를 생성하고 개체명을 추출하는 클래스"""
    
    def __init__(self, stop_words_str):
        """
        TextIndexer 초기화
        
        Args:
            stop_words_str (str): 쉼표로 구분된 제외할 단어 문자열
        """
        self.word_index = defaultdict(lambda: {'count': 0, 'lines': set()})
        self.stop_words = set(word.strip() for word in stop_words_str.lower().split(','))

    def extract_entities_hf(self, text):
        """
        Hugging Face 파이프라인을 사용하여 개체명을 추출하고 후처리 필터링을 수행
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            dict: 개체명 레이블별로 정리된 개체명 목록
        """
        try:
            # 모델이 처리할 수 있는 최대 길이로 텍스트를 분할하여 처리
            max_chunk_size = 512
            words = text.split()
            chunks = [" ".join(words[i:i + max_chunk_size]) for i in range(0, len(words), max_chunk_size)]

            # 각 청크에 대해 NER 수행
            ner_results = []
            for chunk in chunks:
                ner_results.extend(ner_pipeline(chunk))

            entities = defaultdict(set)
            
            # 필터링할 일반적인 단어/칭호 목록
            common_words_to_exclude = {
                'doctor', 'constable', 'countess', 'duke', 'lady', 'angel', 'god', 
                'sir', 'madam', 'miss', 'mister', 'king', 'queen', 'lord', 'father',
                'mother', 'brother', 'sister', 'friend'
            }
            
            # 모델 레이블을 표준 레이블로 매핑
            label_map = {"PER": "PERSON", "LOC": "GPE"}

            # 개체명 추출 및 필터링
            for entity in ner_results:
                label = label_map.get(entity['entity_group'])
                if label:
                    # 불필요한 '#' 및 앞뒤 공백/구두점 제거
                    clean_word = entity['word'].replace('#', '').strip().strip('.,-')
                    
                    # 필터링 조건 적용
                    # 1. 단어가 비어있지 않고
                    # 2. 길이가 2보다 크고 (3글자 이상)
                    # 3. 제외 목록에 포함되지 않은 경우
                    if clean_word and len(clean_word) > 2 and clean_word.lower() not in common_words_to_exclude:
                        entities[label].add(clean_word)

            # 정렬된 리스트로 변환하여 반환
            return {label: sorted(list(names)) for label, names in entities.items()}
        
        except Exception as e:
            print(f"Hugging Face NER Error: {e}")
            return {}

    def build_index(self, text):
        """
        텍스트를 분석하여 단어 인덱스, 통계, 개체명을 생성
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            dict: 분석 결과 (통계, 인덱스, 개체명, 문장 목록)
        """
        # 단어 인덱싱
        total_word_count = 0
        lines = text.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # 영문 단어 추출
            words = re.findall(r"\b[a-z'']+\b", line.lower())
            
            for word in words:
                total_word_count += 1
                cleaned_word = word.strip("''")
                
                # 불용어가 아니고 길이가 1보다 큰 단어만 인덱싱
                if cleaned_word and cleaned_word not in self.stop_words and len(cleaned_word) > 1:
                    self.word_index[cleaned_word]['count'] += 1
                    self.word_index[cleaned_word]['lines'].add(line_num)
        
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)([\.?!][\"\'”’]?)(?!\s+[A-Z]\.)(\s+)'
        text_with_marker = re.sub(pattern, r'\1<SPLIT>', text)
        sentences = text_with_marker.split('<SPLIT>')
        
        # 유효한 문장만 필터링 (2단어 이상)
        valid_sentences = [s.strip() for s in sentences if len(s.strip().split()) > 1]
        
        # 가장 짧은/긴 문장 찾기
        shortest_sentence = min(valid_sentences, key=len) if valid_sentences else ""
        longest_sentence = max(valid_sentences, key=len) if valid_sentences else ""

        # NER 수행
        extracted_entities = self.extract_entities_hf(text)

        # 단어 인덱스를 정렬된 리스트로 변환
        index_list = sorted([
            (word, {'count': data['count'], 'lines': sorted(list(data['lines']))})
            for word, data in self.word_index.items()
        ])

        # 분석 결과 반환
        return {
            "stats": {
                "totalWords": total_word_count,
                "uniqueWords": len(self.word_index),
                "shortestSentence": shortest_sentence,
                "longestSentence": longest_sentence
            },
            "index": index_list,
            "entities": extracted_entities,
            "sentences": valid_sentences
        }

# --- Flask 애플리케이션 설정 ---
app = Flask(__name__)

@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """
    텍스트 파일 분석 API 엔드포인트
    
    Returns:
        JSON: 분석 결과 또는 에러 메시지
    """
    try:
        # 파일 업로드 확인
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file:
            # 파일 내용 읽기
            file_content = file.read().decode('utf-8')
            
            # 불용어 가져오기
            stop_words = request.form.get('stopWords', '')
            
            # 텍스트 분석 수행
            indexer = TextIndexer(stop_words)
            analysis_result = indexer.build_index(file_content)
            
            return jsonify(analysis_result)
    
    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({"error": "An error occurred during analysis."}), 500

if __name__ == '__main__':
    app.run(debug=True)