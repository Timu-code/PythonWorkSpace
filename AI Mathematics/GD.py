# Diffrential of f
def diff(f):
    h = 1e-6
    return lambda x: (f(x + h) - f(x - h)) / (2 * h)

# Objective function
def f(x):
    return 3 * ((x - 5) ** 2) + 2

# Check wheter the optimal solution converges
def is_converged(x_prev, x, threshold):
    return abs(x - x_prev) < threshold

# Gradient Descent algorithm
def gradient_descent(f):
    lr = 0.01
    x = 100
    threshold = 1e-8
    t = 1
    
    while True:
        x_prev = x
        
        x -= (lr * diff(f)(x))
        
        t += 1
        
        print(x)
                
        if is_converged(x_prev, x, threshold):
            break
        
    return x

# Main function
def main():
    gradient_descent(f)
    
if __name__ == '__main__':
    main()