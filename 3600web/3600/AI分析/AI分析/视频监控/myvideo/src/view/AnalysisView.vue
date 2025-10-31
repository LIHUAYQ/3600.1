<script setup>
import {ref, onMounted} from "vue"; // 新增 onMounted
import html2canvas from "html2canvas"; // 导入截图库
import Ation from "@/components/Ation.vue";
import Advice from "@/components/Advice.vue";
import { partdata } from "@/data/data.js";
import {global} from "@/main.js";
import { ElMessage } from 'element-plus'

const pngUrl=ref(global.$config.serverUrl+"static/frontend_screenshot/screenshot_with_bboxes.png")
let part2data = ref()
let part2TableData = []
let part3data = ref()
let part3TableData = []
let key = ref('')
let row = ref({})
let part4data = ref()
let part4TableData = []
let key4 = ref('')
let row4 = ref({})

// 调试参数
const part2_summary = ref(
  "| 隐患类别         | 隐患位置               | 风险等级 | 数量 |\n" +
  "|------------------|----------------------------|----------|------|\n" +
  "| 无     | 无     | 无       | 0    |");
const part3_details = ref("第三部分：隐患详情分析\n" +
  "1. **环境安全隐患**\n" +
  "   - 规范条款：《建筑施工安全检查标准》(JGJ59-2011)第3.2.3条“施工现场应设置密闭式垃圾站，施工垃圾、生活垃圾分类存放，施工垃圾及时清运，保持现场整洁”。\n " +
  "  - 可能后果：垃圾堆积易滋生蚊蝇、传播疾病；垃圾中的易燃物（如木材、油漆桶）可能引发火灾；溢出垃圾堵塞消防通道，影响应急疏散。\n" +
  "\n" +
  "2. **设备安全隐患**\n" +
  "   - 规范条款：《施工现场临时用电安全技术规范》(JGJ46-2005)第8.1.3条“办公区、生活区设备应规范摆放，线缆不得乱拉乱接”。\n" +
  "   - 可能后果：设备线缆杂乱易导致绊倒事故；未规范存放可能造成设备损坏，影响正常使用；堆积杂物遮挡设备散热口，引发设备过热故障。");
const part4_advice = ref("第四部分：安全建议\n" +
  "1. **针对环境安全隐患整改措施**\n" +
  "   - 立即组织人员清理垃圾房内溢出垃圾，分类存放至指定地点，确保垃圾不超过容器容量的2/3。\n" +
  "   - 每日下班前检查垃圾房卫生，设置“日产日清”标识，与环卫部门签订定期清运协议。\n" +
  "   - 在垃圾房周边设置防火沙箱和灭火器，远离易燃材料堆放区，张贴“禁止吸烟”“禁止堆放易燃物”警示标识。\n" +
  "\n" +
  "2. **针对设备安全隐患整改措施**\n" +
  "   - 规范摆放键盘、显示器等设备，保持操作区域整洁，线缆采用理线器或线槽固定，避免裸露和缠绕。\n" +
  "   - 对办公设备进行定期检查，清理设备表面积尘，确保散热孔畅通，发现线缆破损立即更换。\n" +
  "   - 划分设备存放区与通道区域，通道宽度不小于0.8米，设置黄色警示胶带标识通道边界。");

// 初步解析数据
const part2 = async () => {
  const part2List = part2_summary.value.split("\n");
  part2List.forEach((item, index) => {
    part2List[index] = item.split('|').map(item => item.trim()).filter(item => item !== '' && !item.includes('-'));
  })
  part2data.value = part2List.filter(item => item.length > 0);
}

// 进一步处理数据
const part2ToList = () => {
  for (let i = 1; i < part2data.value.length; i++) {
    const row = {}
    for (let j = 0; j < 3; j++) {
      row[part2data.value[0][j]] = part2data.value[i][j]
    }
    part2TableData.push(row)
  }
}

// 调用数据分析
const part222 = () => {
  if (JSON.parse(sessionStorage.getItem("part2_summary"))){
    part2TableData = JSON.parse(sessionStorage.getItem("part2_summary"));
  }else {
    if (partdata.sendpart2_summary !== '') {
      if (partdata.sendpart2_summary!==""){
        part2_summary.value = partdata.sendpart2_summary;
      }
    }
    part2()
    part2ToList()
    sessionStorage.setItem("part2_summary", JSON.stringify(part2TableData),{ deep: true })
  }
}

// 第三部分、第四部分原有逻辑保持不变...

// 初步解析数据
const part3 = () => {
  const part3List = part3_details.value.split("\n");
  part3List.forEach((item, index) => {
    part3List[index] = item.replace(/\*/g, "").replace("- ", "").trim();
  })
  part3data.value = part3List.filter(item => item.length > 0);
}

// 进一步处理数据
const part3ToList = () => {
  let count=0;
  for (let i = 0; i < part3data.value.length; i++) {
    if (part3data.value[i].includes(part2TableData[count]['隐患类别'])) {
      row.value = {}
      key.value = part3data.value[i]
      if (count!==part2TableData.length-1){
        count=count+1
      }
    } else {
      const list = []
      for (let j = i; j < part3data.value.length; j++) {
        if (part3data.value[j].includes(part2TableData[count]['隐患类别'])) {
          i = j - 1
          break
        }
        list.push(part3data.value[j])
        if (j === part3data.value.length - 1) {
          i = j
        }
      }
      row.value[key.value] = list
      part3TableData.push(row.value)
    }
  }
}

// 调用数据分析
const part333 = () => {
  if (JSON.parse(sessionStorage.getItem("part3_details"))){
    part3TableData = JSON.parse(sessionStorage.getItem("part3_details"));
  }else {
    if (partdata.sendpart3_details !== '') {
      part3_details.value = partdata.sendpart3_details
      part3()

      part3ToList()

      sessionStorage.setItem("part3_details", JSON.stringify(part3TableData),{ deep: true })
    }
  }
}

// 初步解析数据
const part4 = () => {
  const part4List = part4_advice.value.split("\n");
  part4List.forEach((item, index) => {
    part4List[index] = item.replace(/\*/g, "").replace("-", "").replace(/#/g, "").trim();
  })
  part4data.value = part4List.filter(item => item.length > 0);
}

// 进一步处理数据
const part4ToList = () => {
  let count=0;
  for (let i = 0; i < part4data.value.length; i++) {
    if (part4data.value[i].includes(part2TableData[count]['隐患类别'])) {
      row4.value = {}
      key4.value = part4data.value[i]
      if (count!==part2TableData.length-1){
        count=count+1
      }
    } else {
      const list = []
      for (let j = i; j < part4data.value.length; j++) {
        if (part4data.value[j].includes(part2TableData[count]['隐患类别'])) {
          i = j - 1
          break
        }
        list.push(part4data.value[j])
        if (j === part4data.value.length - 1) {
          i = j
        }
      }
      row4.value[key4.value] = list
      part4TableData.push(row4.value)
    }
  }
}

// 调用数据分析
const part444 = () => {
  if (JSON.parse(sessionStorage.getItem("part4_advice"))){
    part4TableData = JSON.parse(sessionStorage.getItem("part4_advice"));
  }else {
    if (partdata.sendpart4_advice !== '') {
      part4_advice.value = partdata.sendpart4_advice
      part4()
      part4ToList()
      sessionStorage.setItem("part4_advice", JSON.stringify(part4TableData),{ deep: true })
    }
  }
}

// 统一调用
const partttt = async () => {
  try {
    part222()
    part333()
    part444()
  }catch (error) {
    console.error(error)
    ElMessage.error('网路错误请刷新')
    throw error;
  }
}
partttt()
// -------------------------- 新增：截图下载逻辑 --------------------------
// 1. 给目标截图区域添加 ref（对应 template 中的 analysis-view-box）
const reportRef = ref(null);
// 2. 截图+下载核心函数
const captureAndDownloadReport = async () => {
  try {
    // 等待 DOM 完全渲染（尤其是表格、图片等异步加载内容）
    await new Promise(resolve => setTimeout(resolve, 500));

    // 检查目标元素是否存在
    if (!reportRef.value) {
      console.error("截图目标元素未找到！");
      return;
    }

    // 调用 html2canvas 生成 Canvas（配置项确保截图完整）
    const canvas = await html2canvas(reportRef.value, {
      scale: window.devicePixelRatio, // 用设备像素比，避免模糊同时保证尺寸正确
      useCORS: true,
      logging: false,
      scrollY: -window.scrollY, // 修正滚动偏移（关键！）
      scrollX: -window.scrollX,
      windowWidth: document.documentElement.offsetWidth, // 确保宽度计算正确
      windowHeight: document.documentElement.offsetHeight,
      ignoreElements: (el) => el.style.display === 'none' // 忽略隐藏元素，避免干扰
    });

    // 3. 将 Canvas 转换为 Blob 对象（便于下载）
    canvas.toBlob(blob => {
      // 4. 创建下载链接
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `施工安全隐患报告_${new Date().getTime()}.png`; // 文件名带时间戳，避免重复

      // 5. 触发下载（浏览器需要模拟点击）
      document.body.appendChild(a);
      a.click();

      // 6. 清理资源（避免内存泄漏）
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, "image/png"); // 指定图片格式为 PNG

  } catch (error) {
    console.error("截图失败：", error);
  }
};

// 3. 页面加载完成后自动执行截图（onMounted 确保 DOM 已就绪）
onMounted(() => {
  // 若表格数据是异步获取的（如从 partdata 加载），需确保数据处理完成后再截图
  if (part2TableData.length > 0 && part3TableData.length > 0 && part4TableData.length > 0) {
    captureAndDownloadReport();
  } else {
    // 若数据未就绪，监听数据变化后再截图（可选，应对异步数据）
    const watcher = setInterval(() => {
      if (part2TableData.length > 0 && part3TableData.length > 0 && part4TableData.length > 0) {
        captureAndDownloadReport();
        clearInterval(watcher); // 停止监听
      }
    }, 200);
  }
});

</script>

<template>
  <!-- 关键：给整个报告容器添加 ref="reportRef"，作为截图目标 -->
  <div class="analysis-view-box" ref="reportRef">
    <div class="title-box">
      <h1 style="font-size: 2vw">施工安全隐患检测可视化报告</h1>
    </div>
    <div class="middle-box">
      <div class="img-box">
        <div class="title-p-box"><h4 style="font-size: 1vw">隐患标注图</h4></div>
        <img
          v-if="pngUrl"
          :src="pngUrl"
           alt="隐患现场图片"
           style="width: 42.35vw">
      </div>
      <div class="info-box">
        <div class="info-top-box">
          <div class="title-p-box"><h4 style="font-size: 1vw">隐患汇总</h4></div>
          <el-table
            :data="part2TableData"
            style="width: 24.3vw;height: 15vh"
            :header-cell-style="{color: '#333',width:chosseWidth, fontWeight:'900',textAlign: 'center'}"
            :cell-style="{fontSize:'0.6vw', fontWeight:'600',textAlign: 'center'}"
            v-if="part2TableData.length > 0">
            <el-table-column
              v-for="(item, index) in Object.keys(part2TableData[0] || {})"
              :key="index"
              :prop="item"
              :label="item"
              >
              <template  v-if="item === '风险等级'" #default="scope">
              <span :class="{
                'high-risk': scope.row[item] === '高'||scope.row[item] === '重大隐患'||scope.row[item] === '重大',
                'medium-risk': scope.row[item] === '中'||scope.row[item] === '较大隐患'||scope.row[item] === '较大',
                'yiban-risk': scope.row[item] === '一般隐患'||scope.row[item] === '一般',
                'low-risk': scope.row[item] === '低'||scope.row[item] === '无'||scope.row[item] === '低隐患'||scope.row[item] === '无隐患',
              }">
                {{ scope.row[item]+'风险' }}
              </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="info-bottom-box">
          <div class="title-p-box"><h4 style="font-size: 1vw">隐患安全建议</h4></div>
          <Advice
            v-for="(item, index) in part4TableData"
            :key="index"
            :name="Object.keys(item)[0]"
            :advices="item[Object.keys(item)[0]]">
          </Advice>
        </div>
<!--        <div class="title-p-box"><h4 style="font-size: 1vw">隐患详细分析</h4></div>-->
<!--        <ul>-->
<!--          <Ation-->
<!--            v-for="(item, index) in part3TableData"-->
<!--            :key="index"-->
<!--          :cols="item[Object.keys(item)[0]]"-->
<!--          :name="Object.keys(item)[0]"-->
<!--          :risk-level="part2TableData[index]?.['风险等级']+'风险'">-->
<!--          </Ation>-->
<!--        </ul>-->
<!--      </div>-->
    </div>
    </div>
    <div class="bottom-box">
<!--      <div class="left-box" style="width: 45vw">-->
        <div class="title-p-box"><h4 style="font-size: 1vw">隐患详细分析</h4></div>
        <ul>
          <Ation
            v-for="(item, index) in part3TableData"
            :key="index"
            :cols="item[Object.keys(item)[0]]"
            :name="Object.keys(item)[0]"
            :risk-level="part2TableData[index]?.['风险等级']+'风险'">
          </Ation>
        </ul>
<!--      </div>-->
<!--        <div class="title-p-box"><h4 style="font-size: 1vw">隐患汇总</h4></div>-->
<!--        <el-table-->
<!--          :data="part2TableData"-->
<!--          style="width: 50vw;"-->
<!--          :header-cell-style="{color: '#333',fontSize:'0.7vw', fontWeight:'900',textAlign: 'center'}"-->
<!--          :cell-style="{fontSize:'0.6vw', fontWeight:'600',textAlign: 'center'}"-->
<!--          v-if="part2TableData.length > 0">-->
<!--          <el-table-column-->
<!--            v-for="(item, index) in Object.keys(part2TableData[0] || {})"-->
<!--          :key="index"-->
<!--          :prop="item"-->
<!--          :label="item">-->
<!--          <template  v-if="item === '风险等级'" #default="scope">-->
<!--              <span :class="{-->
<!--                'high-risk': scope.row[item] === '高'||scope.row[item] === '重大隐患'||scope.row[item] === '重大',-->
<!--                'medium-risk': scope.row[item] === '中'||scope.row[item] === '较大隐患'||scope.row[item] === '较大',-->
<!--                'yiban-risk': scope.row[item] === '一般隐患'||scope.row[item] === '一般',-->
<!--                'low-risk': scope.row[item] === '低'||scope.row[item] === '无'||scope.row[item] === '低隐患'||scope.row[item] === '无隐患',-->
<!--              }">-->
<!--                {{ scope.row[item]+'风险' }}-->
<!--              </span>-->
<!--          </template>-->
<!--          </el-table-column>-->
<!--        </el-table>-->
      </div>
<!--      <div class="right-box">-->
<!--        <div class="title-p-box"><h4 style="font-size: 1vw">隐患安全建议</h4></div>-->
<!--        <Advice-->
<!--          v-for="(item, index) in part4TableData"-->
<!--          :key="index"-->
<!--        :name="Object.keys(item)[0]"-->
<!--        :advices="item[Object.keys(item)[0]]">-->
<!--        </Advice>-->
<!--      </div>-->
  </div>
  <p style="font-size: 1vh;text-align: center;color:#333">本报告由AI分析生成，仅供参考</p>
</template>

<style lang="less" scoped>
/* 原有样式保持不变 */
::v-deep .high-risk {
  font-size: 0.6vw;
  background-color: #cc3338;
  color: white;
  padding: 0.2vw 0.8vw;
  border-radius: 0.5vh;


}
::v-deep .yiban-risk {
  font-size: 0.6vw;
  background-color: #d4c306;
  color: white;
  padding: 0.2vw 0.8vw;
  border-radius: 0.5vh;
}
::v-deep .medium-risk {
  font-size: 0.6vw;

  font-weight: 600;
  background-color: #df7724;
  color: white;
  padding: 0.2vw 0.8vw;
  border-radius: 0.5vh;

}
::v-deep .low-risk {
  font-size: 0.6vw;
  background-color: #36d399;
  color:white ;
  padding: 0.2vw 0.8vw;
  border-radius: 0.5vh;
}
.title-p-box {
  margin-bottom: .5vh;
  background-color: #4d6bfc;
  text-align: center;
  line-height: 3vh;
  height: 3vh;
  width: fit-content;
  padding: 0 1vw;
  color: white;
  border-radius: 1vw;
}
.analysis-view-box {
  width: 70vw;
  //height: 98vh;
  //background-color: #f44336;
  //background-color: #6b778c;
  display: flex;
  flex-direction: column;
  //background-color: #4CAF50;
  justify-self: center;
  .title-box {
    position: relative;
    left: -15.02vw;
    width: 100vw;
    height:3.5vw ;
    text-align: center;
    background-color: #4d6bfc;
    color: white;
    h1{
      letter-spacing: 0.5vw;
    }
  }
  .middle-box {
    margin-top: 2vh;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    .img-box {
      background-color:white;
      box-shadow: 0vh 0vh 0.1vh 0.1vh rgba(51, 51, 51, 0.05);
      padding: 1.3vw;
      display: flex;
      flex-direction: column;
      border-radius: 0.5vw;
      img{
        margin-top: 1vh;
      }
    }

    .info-box{
      display: flex;
      flex-direction: column;
      width: 24.3vw;
      box-shadow: 0vh 0vh 0.1vh 0.1vh rgba(51, 51, 51, 0.05);
      background-color:white;
      padding: 1.3vw;
      border-radius: 0.5vw;
      .info-top-box{
        //background-color: #4d6bfc;
        width: 100%;
      }
    }
  }
  .bottom-box {
    box-shadow: 0vh 0vh 0.1vh 0.1vh rgba(51, 51, 51, 0.05);
    background-color:white;
    padding: 1.3vw;
    border-radius: 0.5vw;
    margin-top: 2vh;
    //display: flex;
    //flex-direction: row;
    //justify-content: space-between;
    ul{
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      flex-wrap: wrap;
    }
    .left-box{
      box-shadow: 0vh 0vh 0.1vh 0.1vh rgba(51, 51, 51, 0.05);
      background-color:white;
      padding: 1.3vw;
      border-radius: 0.5vw;
    }
    .right-box{
      width: 24.3vw;
      box-shadow: 0vh 0vh 0.1vh 0.1vh rgba(51, 51, 51, 0.05);
      background-color:white;
      padding: 1.3vw;
      border-radius: 0.5vw;
      //margin-left: 0.7vw;
    }
  }
}
</style>
