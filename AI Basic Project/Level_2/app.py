import time
import json
from flask import Flask, render_template, request, Response, stream_with_context, jsonify

class NQueensSolver:
    """N-Queens/N-Knights 백트래킹 솔버"""
    
    def __init__(self, n, problem_type='queen', obstacles=[]):
        """솔버 초기화"""
        self.n = n
        self.problem_type = problem_type
        self.obstacles = set(tuple(obs) for obs in obstacles)
        
        # N-Queens 문제용
        self.board = [-1] * n 
        
        # N-Knights 문제용
        self.placements = [] 
        
        self.solutions_found = 0
        self.steps_taken = 0
        self.running = True

    # --- 1. N-Queens ---

    def _is_safe_queen_logic(self, row, col):
        """퀸 배치 안전성 검사 (같은 열, 대각선 체크)"""
        for prev_row in range(row):
            prev_col = self.board[prev_row]
            if prev_col == col:
                return False
            if abs(prev_row - row) == abs(prev_col - col):
                return False
        return True

    def _is_safe_queen_master(self, row, col):
        """장애물 및 퀸 배치 안전성 검사"""
        if (row, col) in self.obstacles:
            return False
        
        # N-Queens의 핵심 로직 호출
        return self._is_safe_queen_logic(row, col)

    def _solve_queen(self, row=0):
        """N-Queens 백트래킹 알고리즘"""
        if not self.running:
            return
        
        if row == self.n:
            self.solutions_found += 1
            yield self.format_event(type="solution", board=self.board.copy(), count=self.solutions_found)
            return
        
        for col in range(self.n):
            if not self.running:
                return
            
            self.steps_taken += 1
            
            # 장애물을 포함한 마스터 안전성 검사 함수 호출
            if self._is_safe_queen_master(row, col):
                self.board[row] = col
                yield self.format_event(type="step", board=self.board.copy(), place_row=row, place_col=col, safe=True)
                
                yield from self._solve_queen(row + 1)
                
                yield self.format_event(type="step", board=self.board.copy(), place_row=row, place_col=col, safe=False, backtracking=True)
                self.board[row] = -1
            
            else:
                yield self.format_event(type="step", board=self.board.copy(), place_row=row, place_col=col, safe=False)

            if self.steps_taken % 1000 == 0:
                yield self.format_event(type="ping", steps=self.steps_taken)

    # --- 2. N-Knights ---

    def _is_safe_knight(self, r, c):
        """나이트 배치 안전성 검사 (기존 나이트와 공격 관계 체크)"""
        if (r, c) in self.obstacles:
            return False
        
        for (pr, pc) in self.placements:
            dr, dc = abs(r - pr), abs(c - pc)
            if (dr == 2 and dc == 1) or (dr == 1 and dc == 2):
                return False
        return True

    def _solve_knight(self, k=0, start_index=0):
        """N-Knights 백트래킹 알고리즘"""
        if not self.running:
            return
        
        if k == self.n:
            self.solutions_found += 1
            yield self.format_event(type="solution", board_placements=self.placements.copy(), count=self.solutions_found)
            return

        for i in range(start_index, self.n * self.n):
            if not self.running:
                return

            self.steps_taken += 1
            if self.steps_taken % 1000000 == 0:
                yield self.format_event(type="ping", steps=self.steps_taken)
            
            r, c = divmod(i, self.n)
            
            if self._is_safe_knight(r, c):
                self.placements.append((r, c))
                yield from self._solve_knight(k + 1, i + 1)
                
                if not self.running: return
                self.placements.pop()

    def solve(self):
        """문제 유형별 솔버 실행"""
        if self.problem_type == 'queen':
            yield from self._solve_queen(row=0)
        elif self.problem_type == 'knight':
            yield from self._solve_knight(k=0, start_index=0)

    def format_event(self, **data):
        """SSE(Server-Sent Events) 형식으로 이벤트 포맷팅"""
        return f"data: {json.dumps(data)}\n\n"

current_solver = None
app = Flask(__name__)

@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html')

@app.route('/solve')
def solve_queens():
    """백트래킹 탐색 시작 엔드포인트"""
    global current_solver
    
    n = request.args.get('n', 8, type=int)
    problem_type = request.args.get('problem_type', 'queen', type=str)
    obstacles_str = request.args.get('obstacles', '[]', type=str)
    
    try:
        obstacles = json.loads(obstacles_str)
    except json.JSONDecodeError:
        obstacles = []
    
    # N 크기 제한 (성능 고려)
    if problem_type == 'knight' and n > 8:
         return "N is too large for general Knight problem (max 8)", 400
    if problem_type == 'queen' and n > 16:
        return "N is too large for Queen problem (max 16)", 400
        
    current_solver = NQueensSolver(n, problem_type, obstacles)
    
    @stream_with_context
    def event_stream():
        """SSE 이벤트 스트림 생성기"""
        start_time = time.time()
        try:
            yield from current_solver.solve()
        except GeneratorExit:
            print("스트림이 클라이언트에 의해 중단되었습니다.")
        finally:
            end_time = time.time()
            total_time = end_time - start_time
            yield current_solver.format_event(
                type="done",
                count=current_solver.solutions_found,
                steps=current_solver.steps_taken,
                time=total_time
            )
            print(f"N={n} ({problem_type}, obs: {len(obstacles)}) 완료. "
                  f"총 {current_solver.solutions_found}개의 해, "
                  f"{current_solver.steps_taken} 스텝, {total_time:.2f}초")
            
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/stop', methods=['POST'])
def stop_solver():
    """탐색 중단 엔드포인트"""
    global current_solver
    if current_solver:
        current_solver.running = False
        print("멈춤 신호 수신. 탐색을 중지합니다.")
    return jsonify({"status": "stopping"})

if __name__ == '__main__':
    app.run(debug=True, threaded=True)