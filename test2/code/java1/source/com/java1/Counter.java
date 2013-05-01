package com.java1;

public class Counter
{
    int m_value;
    Inner m_inner;

    public int increment()
    {
        return m_value++;
    }

    public Inner getInner()
    {
        return m_inner;
    }

    public class Inner
    {
        float value;
        void foo()
        {
            switch ((int)value) {
                case 1:
                    System.out.println("1");
                case 2:
                    System.out.println("2");
            }
        }
    }
}
