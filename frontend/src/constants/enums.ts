export const Roles={admin:'站长 / 审批',analyst:'农艺师 / 研究',viewer:'观察员 / 只读'} as const;
export const RunStatus={queued:'排队中',running:'计算中',succeeded:'已完成',failed:'运行失败'} as const;
export const ReviewStatus={pending:'待复查',approved:'已批准',rejected:'已退回'} as const;
