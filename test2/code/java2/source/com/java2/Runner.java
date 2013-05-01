package com.java2;
import com.java1.*;

public class Runner
{
    Counter m_counter;

    public void count()
    {
        Counter.Inner inner = m_counter.getInner();
        m_counter.increment();
    }
}
