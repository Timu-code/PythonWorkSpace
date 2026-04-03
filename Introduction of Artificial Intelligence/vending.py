input_cost = int(input('금액 입력>'))
n = int(input('커피 구매량 입력>'))
output_cost = input_cost - (150 * n)

print(f'거스름 금액: {output_cost}')
print(f'천원 {(output_cost // 1000)} 오백원 {(output_cost % 1000) // 500} 백원 {((output_cost % 1000) % 500) // 100} 오십원 {(((output_cost % 1000) % 500) % 100) // 50} 십원 {(((output_cost % 1000) % 500) % 100) % 50}')