import sys

n, k = map(int, sys.stdin.readline().strip().split())
nums = map(int, sys.stdin.readline().strip().split())

nums = sorted(nums, reverse=True)
temp_sum = 0

sums = sum(nums)

for i in range(k):
    if len(nums) > 0:
        num = nums.pop()
        print(num)
        nums = [(i - num if i != 0 else i) for i in nums]

        if i != k - 1:
            flag = True
            for num in nums:
                if num != 0:
                    flag = False
                    break
            if flag:
                print(0)
                break
    else:
        break
