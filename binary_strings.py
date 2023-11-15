# testInput2 = "00110011"
testInput2 = "01101001"


def countSubstrings(input):
    n = len(input)
    result = 0
    for i in range(1, n):
        left, right = i - 1, i
        initLeft, initRight = input[left], input[right]
        while (
            input[left] != input[right]
            and input[left] == initLeft
            and input[right] == initRight
        ):
            left -= 1
            right += 1
            result += 1
            if left < 0 or right > n - 1:
                break
    return result


print(countSubstrings(testInput2))
