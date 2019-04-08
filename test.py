import sys

n, k = map(int, sys.stdin.readline().strip().split())
nums = map(int, sys.stdin.readline().strip().split())

nums = sorted(nums, reverse=True)
temp_sum = 0

for i in range(k):
    if len(nums) > 0:
        num = nums.pop()
        if num == 0 or num - temp_sum == 0:
            continue
        print(num - temp_sum)
        temp_sum += (num - temp_sum)

        if len(nums)!=0:
            num = 0
            target = len(nums)
            while len(nums) > 0 and (nums[-1] == temp_sum or nums[-1] == 0):
                num += 1
                nums.pop()

            if num == target:
                print(0)
    else:
        break
