/**
 * Responsive Layout Components
 * 响应式布局组件 - 移动端适配
 */
import React, { useState, useEffect, ReactNode } from 'react';
import { Menu, X, ChevronDown, Home, Settings, BarChart3, MessageSquare, Briefcase, GraduationCap } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useNavigate, useLocation } from 'react-router-dom';

// Breakpoints
export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

// Hook to detect mobile
export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < breakpoints.md);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return isMobile;
}

// Hook to detect screen size
export function useBreakpoint() {
  const [breakpoint, setBreakpoint] = useState<'sm' | 'md' | 'lg' | 'xl' | '2xl'>('sm');

  useEffect(() => {
    const checkBreakpoint = () => {
      const width = window.innerWidth;
      if (width >= breakpoints['2xl']) setBreakpoint('2xl');
      else if (width >= breakpoints.xl) setBreakpoint('xl');
      else if (width >= breakpoints.lg) setBreakpoint('lg');
      else if (width >= breakpoints.md) setBreakpoint('md');
      else setBreakpoint('sm');
    };

    checkBreakpoint();
    window.addEventListener('resize', checkBreakpoint);
    return () => window.removeEventListener('resize', checkBreakpoint);
  }, []);

  return breakpoint;
}

// Navigation items
const navItems = [
  { icon: Home, label: '仪表盘', path: '/' },
  { icon: Briefcase, label: 'Fiverr 运营', path: '/fiverr' },
  { icon: BarChart3, label: '社交媒体', path: '/social' },
  { icon: GraduationCap, label: '知识管理', path: '/knowledge' },
  { icon: MessageSquare, label: '消息中心', path: '/messages' },
  { icon: Settings, label: '设置', path: '/settings' },
];

interface ResponsiveSidebarProps {
  children: ReactNode;
}

export function ResponsiveSidebar({ children }: ResponsiveSidebarProps) {
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(!isMobile);

  useEffect(() => {
    if (!isMobile) {
      setIsOpen(true);
    }
  }, [isMobile]);

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) {
      setIsOpen(false);
    }
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800">
      {/* Logo */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-800">
        <h1 className="text-2xl font-bold text-blue-600">AgentForge</h1>
        <p className="text-xs text-gray-500 mt-1">AI 驱动的个人助理</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <button
              key={item.path}
              onClick={() => handleNavigate(item.path)}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
          <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
            U
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm truncate">User Name</p>
            <p className="text-xs text-gray-500 truncate">user@example.com</p>
          </div>
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        {/* Mobile Header */}
        <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between p-4">
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="w-6 h-6" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 p-0">
                <SidebarContent />
              </SheetContent>
            </Sheet>

            <h1 className="text-xl font-bold text-blue-600">AgentForge</h1>

            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
              U
            </div>
          </div>
        </header>

        {/* Mobile Content */}
        <main className="pt-16 min-h-screen">
          {children}
        </main>
      </>
    );
  }

  // Desktop layout
  return (
    <div className="flex min-h-screen">
      <aside className={cn(
        'w-64 fixed left-0 top-0 bottom-0 transition-all duration-300',
        isOpen ? 'translate-x-0' : '-translate-x-64'
      )}>
        <SidebarContent />
      </aside>

      <main className={cn(
        'flex-1 transition-all duration-300',
        isOpen ? 'ml-64' : 'ml-0'
      )}>
        {children}
      </main>
    </div>
  );
}

// Responsive Grid Component
interface ResponsiveGridProps {
  children: ReactNode;
  className?: string;
  cols?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: 'sm' | 'md' | 'lg';
}

export function ResponsiveGrid({ 
  children, 
  className,
  cols = { sm: 1, md: 2, lg: 3, xl: 4 },
  gap = 'md'
}: ResponsiveGridProps) {
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
  };

  const colClasses = {
    sm: cols.sm === 1 ? 'grid-cols-1' : `grid-cols-${cols.sm}`,
    md: cols.md ? `md:grid-cols-${cols.md}` : '',
    lg: cols.lg ? `lg:grid-cols-${cols.lg}` : '',
    xl: cols.xl ? `xl:grid-cols-${cols.xl}` : '',
  };

  return (
    <div className={cn(
      'grid',
      gapClasses[gap],
      Object.values(colClasses).filter(Boolean).join(' '),
      className
    )}>
      {children}
    </div>
  );
}

// Responsive Card Component
interface ResponsiveCardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function ResponsiveCard({ 
  children, 
  className,
  padding = 'md'
}: ResponsiveCardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4 md:p-6',
    lg: 'p-6 md:p-8',
  };

  return (
    <div className={cn(
      'bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800',
      paddingClasses[padding],
      className
    )}>
      {children}
    </div>
  );
}

// Mobile-optimized Stat Card
interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ElementType;
  className?: string;
}

export function StatCard({ title, value, change, icon: Icon, className }: StatCardProps) {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <div className={cn(
        'bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white',
        className
      )}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-blue-100 text-xs font-medium">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {change !== undefined && (
              <p className={cn(
                'text-xs mt-1',
                change >= 0 ? 'text-green-200' : 'text-red-200'
              )}>
                {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
              </p>
            )}
          </div>
          <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      'bg-white dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-800',
      className
    )}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold mt-2 text-gray-900 dark:text-white">{value}</p>
          {change !== undefined && (
            <p className={cn(
              'text-sm mt-2',
              change >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {change >= 0 ? '↑' : '↓'} {Math.abs(change)}% from last month
            </p>
          )}
        </div>
        <div className="w-14 h-14 rounded-full bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
          <Icon className="w-7 h-7 text-blue-600 dark:text-blue-400" />
        </div>
      </div>
    </div>
  );
}

// Touch-friendly Button
interface TouchButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ElementType;
}

export function TouchButton({ 
  children, 
  variant = 'default',
  size = 'md',
  icon: Icon,
  className,
  ...props 
}: TouchButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    default: 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-700',
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800',
    ghost: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',
    md: 'px-4 py-3 text-base min-h-[44px]',
    lg: 'px-6 py-4 text-lg min-h-[52px]',
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {Icon && <Icon className={cn('mr-2', children ? 'w-5 h-5' : 'w-6 h-6')} />}
      {children}
    </button>
  );
}

// Swipeable Card for Mobile
interface SwipeableCardProps {
  children: ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  className?: string;
}

export function SwipeableCard({ 
  children, 
  onSwipeLeft, 
  onSwipeRight,
  className 
}: SwipeableCardProps) {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;

    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft();
    }

    if (isRightSwipe && onSwipeRight) {
      onSwipeRight();
    }
  };

  return (
    <div
      className={cn(
        'touch-pan-y',
        className
      )}
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      {children}
    </div>
  );
}

export default ResponsiveSidebar;
