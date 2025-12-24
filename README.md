# 简介
基于seleniumbase框架改的UI自动化测试框架，对部分方法做了封装  
将测试用例集按pytest的用例格式写，写完丢进test_cases文件夹内即可  
举个例子：  
比如H5_tmall_test.py就是一个用例集，其中的test_XXX函数属于用例，一个用例集里面可以有多条用例都会被执行  
运行run_test.py会执行test_cases中所有用例集  
运行的时候会根据用例集名称里面是否带_H5或者_mobile来判定是模拟手机端的页面，还是常规桌面端，启动不同尺寸的浏览器  
开启运行后会分别启动一个线程运行2个端的用例，等待所有线程运行完毕后，统一输出测试结果到企微  
## 运行结果
配置企微的webhook后，会将执行结果统计完后，统一下发  
<img width="299" height="405" alt="image" src="https://github.com/user-attachments/assets/00dd6bdb-26f7-45e9-96dc-623ae59c4c47" />
