<template>

  <div class="master-detail-view">
    <div class="left-column">
      <div class="control">
        <router-link class="control-link" :to="{'name': this.addAction}">+</router-link>
      </div>
      <div class="item selected">Hi</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
      <div class="item">World</div>
    </div>
    <div class="detail-column">
      <router-view></router-view>
    </div>
  </div>

</template>

<script>
export default {
  name: "master-detail-view",
  props: {
    items: {
      type: Object,
      default: function() {

      }
    },
    addAction: {
      type: String,
      default: "Add"
    },
  },
  methods: {
    goToAdd: () => {
      this.$router.push(this.addAction);
    },
    /*goToAdd: () => {
      this.$route.push(this.addAction);
    },*/
  },
};

</script>

<style scoped>

  .master-detail-view {
    /* Rectangle: */
    background: #06B06D;
    box-shadow: 0 2px 4px 0 rgba(175,175,175,0.50);
    /* Rectangle: */
    /* Initial Setup: */
    font-size: 20px;
    color: #272727;
    letter-spacing: 0.12px;
    width: 100%;
    min-height: 100px;
    margin: auto auto auto auto;
    margin-top: 15px;
    padding: 0px 0px 0px 0px;
    display: flex;
    flex-direction: row;
    align-items: stretch;
  }

  .left-column {
    min-height: 55px;
    flex-basis:20%;
    text-align: right;
    padding-top: 10px;
    display: flex;
    flex-direction: column;
  }

  .item {
    background: #F6F5F5;
    padding-right: 15px;
    border-right: 1px solid rgba(175,175,175,0.50);
    border-top: 1px solid rgba(175,175,175,0.125);
    padding-top: 5px;
    padding-bottom: 5px;
  }

  .detail-column {
    background: #F6F5F5;
    flex-basis: 100%;
    text-align: justify;
    padding-top: 2px;
    padding-left: 15px;
  }

  .last {
    box-shadow: 2px 2px 4px -1px rgba(56,56,56,0.50);

  }

  .control {
    padding-right: 15px;

  }

  .control-link {
    color: white;
    font-weight: bold;
    text-decoration: none;
  }

  .selected {
    font-weight: bold;
  }

</style>
