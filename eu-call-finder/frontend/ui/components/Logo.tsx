import React from 'react';

const Logo: React.FC = () => {
  return (
    <div className="flex items-center gap-3 group cursor-pointer">
      {/* Animated Logo Container */}
      <div className="relative">
        {/* Outer rotating ring */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary via-eu-yellow to-primary opacity-70 blur-sm animate-spin-slow group-hover:animate-spin"></div>
        
        {/* Middle pulsing ring */}
        <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-eu-yellow via-primary to-eu-yellow opacity-50 blur-md animate-pulse-slow"></div>
        
        {/* Main logo background */}
        <div className="relative bg-gradient-to-br from-primary to-eu-blue p-2.5 rounded-xl shadow-lg transform transition-all duration-500 group-hover:scale-110 group-hover:rotate-3">
          <span className="material-icons text-white text-2xl">account_balance</span>
        </div>
        
        {/* Floating particles */}
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-eu-yellow rounded-full animate-bounce delay-100"></div>
        <div className="absolute -bottom-1 -left-1 w-1.5 h-1.5 bg-primary rounded-full animate-bounce delay-300"></div>
      </div>
      
      {/* Animated Text */}
      <div className="flex flex-col">
        <span className="font-bold text-2xl tracking-tight text-eu-blue dark:text-white relative overflow-hidden">
          <span className="relative z-10">EuroFund</span>
          <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></span>
        </span>
        <span className="font-bold text-xl text-primary relative">
          Finder
          <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-eu-yellow group-hover:w-full transition-all duration-500"></span>
        </span>
      </div>
    </div>
  );
};

export default Logo;
