import React from "react";

const SignalCard = ({ title, value }) => (
  <div className="bg-slate-800 rounded-2xl shadow-md p-4 m-2 w-64">
    <h3 className="text-xl font-bold mb-2">{title}</h3>
    <p className="text-3xl">{value}</p>
  </div>
);

export default SignalCard;
