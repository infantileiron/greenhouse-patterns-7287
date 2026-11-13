export const Roles={admin:'站长 / 审批',analyst:'农艺师 / 研究',viewer:'观察员 / 只读'} as const;
export const RunStatus={queued:'排队等待',running:'处理中',recovering:'恢复重试',succeeded:'已完成',failed:'运行失败'} as const;
export const ReviewStatus={pending:'待复查',approved:'已批准',rejected:'已退回'} as const;
