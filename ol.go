// implement ye olde ol command in go

package main

import (
	"fmt"
)

func main() {
	var s string
	var ok bool

	i := 7
	m := map[int]string{1: "hi"}

	if s, ok = m[1]; !ok {
		fmt.Println("you have a career at microsoft")
	}

	fmt.Printf("%q %q\n", m[1], s)

	if true {
		i := 13
		fmt.Printf("i is %v!\n", i)
	}

	{
		i := 36
		fmt.Printf("i is %v!\n", i)
	}

	fmt.Printf("i is %v!\n", i)

	fmt.Println("Hi Tony!")
}
