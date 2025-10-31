<template>
  <div class="risk-item">

    <div class="risk-content">
      <div class="risk-title">
<!--        <span class="risk-code">{{ code }}</span>-->
        <span style="font-size: 1.7vh" class="risk-name">{{ name }}</span>
        <div  :class="riskLevelClass">
          {{ riskLevel }}
        </div>
      </div>
      <div style="font-size: 1.5vh" class="col" v-for="(iteam,index) in cols" :key="index">
        {{ iteam }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  // 风险等级（高风险、中风险、低风险）
  riskLevel: {
    type: String,
    required: true,
  },
  // 风险名称
  name: {
    type: String,
    required: true,
  },
  // 规范条款
  cols:{
    type:Object,
    required:true,
  }
});

// 根据风险等级计算样式类名
const riskLevelClass = computed(() => {
  return {
    'high-risk': props.riskLevel === '高风险'||props.riskLevel === '重大风险'||props.riskLevel === '重大隐患风险',
    'medium-risk': props.riskLevel === '中风险'||props.riskLevel === '较大风险'||props.riskLevel === '较大隐患风险',
    'yiban-risk':props.riskLevel === '一般风险'||props.riskLevel === '一般隐患风险',
    'low-risk': props.riskLevel === '低风险'||props.riskLevel === '无风险'||props.riskLevel === '无隐患风险'||props.riskLevel === '无隐患风险',
  };
});
</script>

<style scoped>
.risk-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1vh;
  padding: 0.7vw;
  border-radius: 0.2vw;
  background-color: #f3f4f8;
}

::v-deep .high-risk {
  font-size: 0.6vw;

  font-weight: 600;
  background-color: #cc3338;
  color: white;
  padding: 0.2vw 0.8vw;
  border-radius: 0.5vh;

}

/* 中风险样式 */
::v-deep .medium-risk {
  font-size: 0.6vw;

  font-weight: 600;
  background-color: #df7724;
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
/* 低风险样式 */
::v-deep .low-risk {
  font-size: 0.6vw;

  font-weight: 600;
  background-color: #36d399;
  color:white ;
  padding: 0.2vw 0.8vw;
  border-radius: 0.5vh;

}

.risk-content {
  width: 32vw;
  //background-color: #4CAF50;
  flex: 1;
}

.risk-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.2vw;
}


.risk-name {
  font-weight: bold;
  font-size: 0.7vw;
}

col{
  margin-bottom: 0.3vw;
  font-size: 0.6vw;
  line-height: 0.7vw;
}
</style>
